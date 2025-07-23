import os
import sys
import warnings
from collections.abc import Generator
from typing import Any

import allure
import pytest
from allure_commons.types import AttachmentType
from dotenv import load_dotenv
from pytest import Item

from niffler_e_2_e_tests_python.fixtures.auth_fixtures import (  # noqa: F401
    api_auth_token,
)
from niffler_e_2_e_tests_python.fixtures.client_fixtures import (  # noqa: F401
    category_api,
    spend_api,
    spend_db,
)
from niffler_e_2_e_tests_python.fixtures.pages_fixtures import (  # noqa: F401
    browser_page,
    login_page,
    main_page,
    new_spending_page,
    profile_page,
)
from niffler_e_2_e_tests_python.fixtures.util_test_fixtures import (  # noqa: F401
    add_and_cleanup_category,
    add_spending,
    category,
    create_test_category_api,
    create_test_spend_api,
    spendings_manager,
)
from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.pages.login_page import LoginPage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from faker import Faker

from niffler_e_2_e_tests_python.pages.main_page import MainPage

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
        username=os.getenv("USERNAME"),
        password=os.getenv("PASSWORD"),
        base_auth_url=os.getenv("BASE_AUTH_URL"),
        base_url=os.getenv("BASE_URL"),
        base_error_url=os.getenv("BASE_ERROR_URL"),
        spend_db_url=os.getenv("SPEND_DB_URL"),
        auth_url=os.getenv("AUTH_URL"),
        auth_secret=os.getenv("AUTH_SECRET"),
        frontend_url=os.getenv("FRONTEND_URL"),
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
def create_user(login_page: LoginPage, create_test_data, envs) -> tuple[str, str]:
    """Фикстура для регистрации нового пользователя через UI.

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
    return username, password


@pytest.fixture(scope="function")
def login(login_page: LoginPage, main_page: MainPage, envs) -> tuple[str, str, str]:
    """Фикстура для авторизации пользователя через UI.

    :param login_page: Объект страницы логина.
    :param main_page: Объект главной страницы.
    :param envs: Конфигурация окружения.
    :return: Кортеж (username, password, token).
    """
    login_page.visit(envs.base_auth_url)
    login_page.input_username.fill(envs.username)
    login_page.input_password.fill(envs.password)
    token = login_page.login_button.click(intercept_header=True)
    main_page.history_of_spending_title.should_be_visible()

    allure.attach(token, name="token.txt", attachment_type=AttachmentType.TEXT)
    return envs.username, envs.password, token
