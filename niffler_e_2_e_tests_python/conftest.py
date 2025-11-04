import os
import sys
import warnings
from collections.abc import Generator
from typing import Any
from uuid import uuid4

import allure
import grpc
import pytest
from allure_commons.types import AttachmentType
from dotenv import load_dotenv
from grpc import insecure_channel
from pytest import Item

from niffler_e_2_e_tests_python.databases.friendship_db import FriendshipDb
from niffler_e_2_e_tests_python.databases.used_db import UsersDb
from niffler_e_2_e_tests_python.grpc_tests.internal.grpc.interceptors.allure import (
    AllureInterceptor,
)
from niffler_e_2_e_tests_python.grpc_tests.internal.grpc.interceptors.logging import (
    LoggingInterceptor,
)
from niffler_e_2_e_tests_python.grpc_tests.internal.pb.niffler_currency_pb2_pbreflect import (
    NifflerCurrencyServiceClient,
)
from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.pages.login_page import LoginPage
from niffler_e_2_e_tests_python.utils.auth_client import AuthClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from faker import Faker

from niffler_e_2_e_tests_python.pages.main_page import MainPage
from niffler_e_2_e_tests_python.utils.kafka_client import KafkaClient

pytest_plugins = [
    "fixtures.auth_fixtures",
    "fixtures.client_fixtures",
    "fixtures.pages_fixtures",
    "fixtures.util_test_fixtures",
    "fixtures.soap_fixtures",
]

fake = Faker()


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_call(item: Item) -> Generator[None, Any]:
    """Pytest-хук, вызываемый после выполнения теста (runtest_call).
    Используется для динамического изменения заголовка теста в Allure-отчёте.

    :param item: Тестовый элемент Pytest, который был вызван.
    :yield: Управление передаётся другим хукам (hookwrapper).
    """

    yield
    allure.dynamic.title(" ".join(item.name.split("_")[1:]).title())


def allure_logger(config: pytest.Config):
    """Безопасно получает Allure-логгер из Pytest-конфигурации.

    :param config: Pytest-конфигурация (pytest.Config).
    :return: Экземпляр AllureReporter, предоставляющий доступ к логированию в Allure, или None, если не найден.
    """
    listener = (
        config.pluginmanager.get_plugin("allure_listener")
        or config.pluginmanager.get_plugin("allure-pytest")
        or config.pluginmanager.get_plugin("allure_pytest")
    )
    if listener is None:
        warnings.warn(
            "[Allure] Плагин allure_listener не найден — шаги фикстуры не будут переименованы.",
            stacklevel=2,
        )
        return None
    return getattr(listener, "allure_logger", None)


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_fixture_setup(fixturedef: pytest.FixtureDef, request: pytest.FixtureRequest):
    """Pytest-хук, вызываемый при инициализации любой фикстуры (fixture_setup).
    Безопасно меняет название шага Setup в Allure-отчёте на более читаемое,
    например, добавляя префикс с областью видимости и красивое имя фикстуры.

    :param fixturedef: Определение фикстуры (FixtureDef), содержит метаданные о фикстуре.
    :param request: Объект запроса фикстуры (FixtureRequest), содержит данные запроса.
    :yield: Управление передаётся другим хукам (hookwrapper).
    """

    yield
    logger = allure_logger(request.config)
    if logger is not None:
        try:
            item = logger.get_last_item()
            scope_letter = fixturedef.scope[0].upper()
            item.name = (
                f"[{scope_letter}] " + " ".join(fixturedef.argname.split("_")).title()
            )
        except Exception as e:
            warnings.warn(
                f"[Allure] Ошибка при переименовании шага фикстуры: {e}", stacklevel=2
            )
    else:
        warnings.warn(
            "[Allure] allure_logger не найден — фикстура будет отображаться с обычным именем.",
            stacklevel=2,
        )


@pytest.fixture(scope="session", autouse=True)
def envs() -> Envs:
    """Глобальная фикстура окружения, подгружает переменные из .env файла и создает объект конфигурации Envs.

    :return: Экземпляр Envs с параметрами окружения.
    """
    load_dotenv()
    env_instance = Envs(
        api_url=os.getenv("API_URL"),
        base_auth_url=os.getenv("BASE_AUTH_URL"),
        base_url=os.getenv("BASE_URL"),
        base_error_url=os.getenv("BASE_ERROR_URL"),
        spend_db_url=os.getenv("SPEND_DB_URL"),
        auth_url=os.getenv("AUTH_URL"),
        auth_secret=os.getenv("AUTH_SECRET"),
        frontend_url=os.getenv("FRONTEND_URL"),
        kafka_address_producer=os.getenv("KAFKA_ADDRESS_PRODUCER"),
        kafka_address_consumer=os.getenv("KAFKA_ADDRESS_CONSUMER"),
        user_db_url=os.getenv("USER_DB_URL"),
        userdata_group_id=os.getenv("USERDATA_GROUP_ID"),
        grpc_address=os.getenv("GRPC_ADDRESS"),
        grpc_mock_address=os.getenv("GRPC_MOCK_ADDRESS"),
        userdata_soap_url=os.getenv("USERDATA_SOAP_URL"),
        userdata_soap_ns=os.getenv("USERDATA_SOAP_NS"),
    )
    allure.attach(
        env_instance.model_dump_json(indent=2),
        name="env.json",
        attachment_type=AttachmentType.JSON,
    )
    return env_instance


@pytest.fixture(scope="function")
def create_test_data() -> tuple[str, str]:
    """Фикстура для генерации тестовых данных пользователя.

    :return: Кортеж (username, password), сгенерированные с помощью Faker.
    """
    username = fake.user_name()
    password = fake.password()
    return username, password


@pytest.fixture(scope="function")
def create_user(
    login_page: LoginPage, create_test_data, envs, db_client
) -> Generator[tuple[str, str], Any]:
    """Фикстура для регистрации нового пользователя через UI.

    :param db_client: Клиент доступа к БД пользователей (`UsersDb`)
    :param login_page: Объект страницы логина.
    :param create_test_data: Кортеж (username, password).
    :param envs: Конфигурация окружения.
    :return: Кортеж (username, password) зарегистрированного пользователя.
    """
    username, password = create_test_data
    login_page.visit(envs.base_auth_url)
    login_page.create_new_account_button.click()
    login_page.input_username.fill(username)
    login_page.input_password.fill(password)
    login_page.input_submit_password.fill(password)
    login_page.sign_up_button.click()
    login_page.congratulations_register_text.should_be_visible()
    login_page.sign_in_link.click()
    login_page.login_title.should_be_visible()
    yield username, password
    db_client.delete_user_by_username_from_users_and_friendship(username)


@pytest.fixture(scope="function")
def login(
    login_page: LoginPage, main_page: MainPage, envs, api_test_user
) -> tuple[str, str, str]:
    """Фикстура для авторизации пользователя через UI.

    :param login_page: Объект страницы логина.
    :param main_page: Объект главной страницы.
    :param envs: Конфигурация окружения.
    :param api_test_user: креды нового пользователя
    :return: Кортеж (username, password, token).
    """
    login_page.visit(envs.base_auth_url)
    login_page.input_username.fill(api_test_user.username)
    login_page.input_password.fill(api_test_user.password)
    token = login_page.login_button.click(intercept_header=True)
    main_page.history_of_spending_title.should_be_visible()

    allure.attach(token, name="token.txt", attachment_type=AttachmentType.TEXT)
    return api_test_user.username, api_test_user.password, token


@pytest.fixture(scope="function")
def auth_client(envs) -> AuthClient:
    """Создаёт и возвращает клиент авторизации для e2e-тестов.

    Фикстура имеет область видимости «function», поэтому для каждого теста используется свой экземпляр клиента
    клиента. Параметры окружения (базовые URL) берутся из фикстуры envs.

    :param envs: Объект окружения с настройками для сервиса авторизации.
    :return: Инициализированный клиент для выполнения запросов к auth-сервису.
    """
    return AuthClient(envs)


@pytest.fixture(scope="session")
def db_client(envs) -> UsersDb:
    """Создаёт клиент доступа к базе данных пользовательских данных.

    Под капотом инициализируется SQLAlchemy/SQLModel-движок и пул соединений.
    Экземпляр переиспользуется всеми тестами в течение одной сессии. Если тестам
    требуется изоляция данных, удаляйте/создавайте записи в самом тесте или
    используйте фабрики.

    :param envs: Объект окружения, содержащий строку подключения к БД.
    :return: Клиент для выполнения запросов к таблицам пользовательских данных.
    """
    return UsersDb(envs.user_db_url)


@pytest.fixture(scope="session")
def friendship_db(envs) -> FriendshipDb:
    """Фикстура уровня сессии для доступа к таблице `friendship` в пользовательской БД.

    Создаёт экземпляр клиента `FriendshipDb`, который обеспечивает методы
    для выборки, добавления, обновления и удаления связей дружбы между пользователями.

    Используется во всех тестах SOAP / Userdata, где требуется верификация
    состояния дружбы в базе данных после вызовов SOAP-методов
    (`sendInvitation`, `acceptInvitation`, `declineInvitation`, `removeFriend`).

    :param envs: Фикстура с объектом `Envs`, содержащим параметры окружения
                 и строку подключения `user_db_url`.
    :return: Экземпляр `FriendshipDb`, готовый к работе с таблицей `friendship`.
    """
    return FriendshipDb(envs.user_db_url)


@pytest.fixture(scope="function")
def kafka(envs, request):
    """Предоставляет Kafka-клиент для публикации и чтения сообщений.

    Открывает подключения продюсера/консьюмера на каждый тест и
    автоматически закрывает их по завершении (контекстный менеджер гарантирует
    закрытие консюмера и flush продюсера). Используйте этот клиент для отправки
    тестовых сообщений и подписки на топики.

    :param request:
    :param envs: Объект окружения с адресами брокеров и прочими настройками.
    :yield: Экземпляр KafkaClient, готовый к взаимодействию с кластером.
    """
    group_id = f"{envs.userdata_group_id}-{request.node.nodeid}-{uuid4().hex[:6]}"
    with KafkaClient(envs, group_id=group_id) as k:
        yield k


INTERCEPTORS = [
    LoggingInterceptor(),
    AllureInterceptor(),
]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавляет пользовательскую опцию командной строки ``--mock`` для pytest.

    Позволяет переключать конфигурацию тестов между реальным окружением и мок-режимом.
    При указании ``--mock`` фикстуры, зависящие от этой опции (например, ``grpc_client``),
    будут использовать альтернативные адреса и ресурсы (например, тестовый gRPC-сервер).

    :param parser: Объект парсера pytest, через который регистрируются пользовательские опции.
    """
    parser.addoption("--mock", action="store_true", default=False)


@pytest.fixture(scope="function")
def grpc_client(request: pytest.FixtureRequest, envs) -> NifflerCurrencyServiceClient:
    """Создаёт gRPC-клиент для взаимодействия с сервисом ``NifflerCurrencyService``.

    Фикстура инициализирует соединение с сервером gRPC один раз на всю сессию тестов.
    Если тесты запущены с опцией ``--mock``, используется альтернативный адрес
    (``envs.grpc_mock_address``) — например, для локального или тестового сервера.
    Для всех вызовов подключаются перехватчики ``LoggingInterceptor`` и ``AllureInterceptor``,
    обеспечивающие логирование и интеграцию с Allure-отчётами.

    :param request: Объект запроса фикстуры pytest, используемый для проверки флага ``--mock``.
    :param envs: Объект окружения с адресами gRPC-серверов и другими настройками.
    :return: Экземпляр ``NifflerCurrencyServiceClient`` с готовым перехваченным каналом.
    """
    channel = insecure_channel(envs.grpc_address)
    if request.config.getoption("--mock"):
        channel = insecure_channel(envs.grpc_mock_address)
    intercepted_channel = grpc.intercept_channel(channel, *INTERCEPTORS)
    return NifflerCurrencyServiceClient(intercepted_channel)
