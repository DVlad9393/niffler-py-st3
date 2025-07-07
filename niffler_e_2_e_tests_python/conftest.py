from allure_commons.reporter import AllureReporter
from allure_commons.types import AttachmentType
from allure_pytest.listener import AllureListener
from dotenv import load_dotenv
import os
import pytest
from pytest import Item

from typing import Any, Generator, Callable

import allure
import sys
import uuid

from niffler_e_2_e_tests_python.databases.spend_db import SpendDB
from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.models.spend import Spend, SpendAdd, SpendDTO, CategoryDTO
from niffler_e_2_e_tests_python.pages.login_page import LoginPage
from niffler_e_2_e_tests_python.pages.profile_page import ProfilePage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from playwright.sync_api import Page, sync_playwright

from niffler_e_2_e_tests_python.pages.main_page import MainPage
from niffler_e_2_e_tests_python.pages.new_spending_page import NewSpendingPage
from datetime import datetime, timezone
from niffler_e_2_e_tests_python.utils.base_session import BaseSession
from niffler_e_2_e_tests_python.utils.utils import SpendApiClient, CategoriesApiClient

from faker import Faker

fake = Faker()

@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_call(item: Item) -> Generator[None, Any, None]:
    """
    Pytest-хук, вызываемый после выполнения теста (runtest_call).
    Используется для динамического изменения заголовка теста в Allure-отчёте.

    :param item: Тестовый элемент Pytest, который был вызван.
    :yield: Управление передаётся другим хукам (hookwrapper).
    """
    yield
    allure.dynamic.title(" ".join(item.name.split("_")[1:]).title())

def allure_logger(config: pytest.Config) -> AllureReporter:
    """
    Получает Allure-логгер из Pytest-конфигурации.

    :param config: Pytest-конфигурация (pytest.Config).
    :return: Экземпляр AllureReporter, предоставляющий доступ к логированию в Allure.
    """
    listener: AllureListener = config.pluginmanager.get_plugin("allure_listener")
    return listener.allure_logger

@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_fixture_setup(fixturedef: pytest.FixtureDef, request: pytest.FixtureRequest) -> Generator[None, Any, None]:
    """
    Pytest-хук, вызываемый при инициализации любой фикстуры (fixture_setup).
    Используется для изменения названия шага Setup в Allure-отчёте на более читаемое,
    например, добавляя префикс с областью видимости и красивое имя фикстуры.

    :param fixturedef: Определение фикстуры (FixtureDef), содержит метаданные о фикстуре.
    :param request: Объект запроса фикстуры (FixtureRequest), содержит данные запроса.
    :yield: Управление передаётся другим хукам (hookwrapper).
    """
    yield
    logger = allure_logger(request.config)
    item: pytest.Item = logger.get_last_item()
    scope_letter = fixturedef.scope[0].upper()
    item.name = f"[{scope_letter}] " + " ".join(fixturedef.argname.split("_")).title()

@pytest.fixture(scope='session', autouse=True)
def envs() -> Envs:
    """
    Глобальная фикстура окружения, подгружает переменные из .env файла и создает объект конфигурации Envs.

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
        spend_db_url=os.getenv("SPEND_DB_URL")
    )
    allure.attach(env_instance.model_dump_json(indent=2), name= "env.json", attachment_type=AttachmentType.JSON)
    return env_instance

@pytest.fixture(scope='function', params=['chromium'])
def browser_page(request) -> Generator[Any, Any, None]:
    """
       Фикстура для создания страницы браузера Playwright.

       :param request: Параметризировано браузером ('chromium', по умолчанию).
       :yields: Экземпляр страницы Playwright Page.
       Делает скриншот и прикладывает видео после завершения теста.
    """
    browser_name = request.param
    with sync_playwright() as playwright:
       browser = getattr(playwright, browser_name).launch(headless=False, args=["--start-maximized", "--window-position=0,0"])
       context = browser.new_context(viewport={"width": 1600, "height": 900}, record_video_dir="allure-results/")
       page = context.new_page()

       yield page

       allure.attach(
           page.screenshot(),
           name='screenshot',
           attachment_type=allure.attachment_type.PNG,
       )

       video = page.video.path()
       page.close()
       context.close()
       allure.attach.file(
           video,
           name="video",
           attachment_type=allure.attachment_type.WEBM,
       )

@pytest.fixture(scope='function')
def main_page(browser_page: Page) -> MainPage:
    """
    Фикстура возвращает объект главной страницы (MainPage) для работы с UI.

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр MainPage.
    """
    return MainPage(browser_page)

@pytest.fixture(scope='function')
def login_page(browser_page: Page) -> LoginPage:
    """
    Фикстура возвращает объект страницы логина (LoginPage).

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр LoginPage.
    """
    return LoginPage(browser_page)

@pytest.fixture(scope='function')
def new_spending_page(browser_page: Page) -> NewSpendingPage:
    """
    Фикстура возвращает объект страницы создания новой траты (NewSpendingPage).

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр NewSpendingPage.
    """
    return NewSpendingPage(browser_page)

@pytest.fixture(scope='function')
def profile_page(browser_page: Page) -> ProfilePage:
    """
    Фикстура возвращает объект страницы профиля (ProfilePage).

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр ProfilePage.
    """
    return ProfilePage(browser_page)

@pytest.fixture(scope='function')
def create_test_data() -> tuple[str, str]:
    """
    Фикстура для генерации тестовых данных пользователя.

    :return: Кортеж (username, password), сгенерированные с помощью Faker.
    """
    username = fake.user_name()
    password = fake.password()
    return username, password

@pytest.fixture(scope='function')
def create_user(login_page: LoginPage, create_test_data, envs) -> tuple[str, str]:
    """
    Фикстура для регистрации нового пользователя через UI.

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

@pytest.fixture(scope='function')
def login(login_page: LoginPage, main_page: MainPage, envs) -> tuple[str, str, str]:
    """
    Фикстура для авторизации пользователя через UI.

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

@pytest.fixture
def spend_api(login, envs) -> Generator[SpendApiClient, Any, None]:
    """
    Фикстура для создания API клиента SpendApiClient с авторизацией.

    :param login: Кортеж с логином и токеном.
    :param envs: Конфигурация окружения.
    :yields: Экземпляр SpendApiClient.
    После завершения теста сессия закрывается.
    """
    token = login[2]
    session = BaseSession(envs.api_url)
    api = SpendApiClient(session, token)
    yield api
    session.close()

@pytest.fixture
def add_spending(spend_api, category, login) -> Callable[[Any, int, Any, str], SpendDTO]:
    """
    Фикстура-обёртка для добавления новой траты.

    :param spend_api: API клиент SpendApiClient.
    :param category: Объект категории.
    :param login: Кортеж (username, ...).
    :return: Внутренняя функция _add_spending для добавления траты через API.
    """
    def _add_spending(description, amount=100, category_name=None, currency="RUB"):
        username = login[0]

        category_obj = category
        if category_name:

            all_categories = spend_api.session.get("/api/categories/all", headers=spend_api.headers).json()
            match = next((c for c in all_categories if c["name"] == category_name), None)
            if not match:

                match = spend_api.session.post("/api/categories/add", json={
                    "name": category_name,
                    "username": username
                }, headers=spend_api.headers).json()
            category_obj = CategoryDTO(**match)
        spend = SpendAdd(
            id=str(uuid.uuid4()),
            spendDate=datetime.now(timezone.utc),
            category=category_obj,
            currency=currency,
            amount=amount,
            description=description
        )

        return spend_api.add_spending(spend, category_obj, username)
    return _add_spending

@pytest.fixture
def spendings_manager(login, envs) -> Generator[Any, Any, None]:
    """
    Фикстура-менеджер для создания и очистки трат. После завершения теста удаляет созданные траты.

    :param login: Кортеж с логином и токеном.
    :param envs: Конфигурация окружения.
    :yields: Кортеж (spend_api, created_spendings).
    """
    token = login[2]
    session = BaseSession(envs.api_url)
    spend_api = SpendApiClient(session, token)
    created_spendings = []

    yield spend_api, created_spendings

    spends = spend_api.get_all_spends()
    ids_to_delete = [
        s.id for s in spends if s.description in created_spendings
    ]
    if ids_to_delete:
        spend_api.delete_spending(ids_to_delete)
    session.close()

@pytest.fixture(scope='session')
def spend_db(envs) -> SpendDB:
    """
    Фикстура для подключения к базе данных трат.

    :param envs: Конфигурация окружения.
    :return: Экземпляр SpendDB.
    """
    return SpendDB(envs.spend_db_url)

@pytest.fixture()
def category(login, envs, spend_db) -> Generator[CategoryDTO, Any, None]:
    """
    Фикстура для получения/создания тестовой категории (по умолчанию 'TestCat').
    После завершения теста удаляет созданную категорию из БД.

    :param login: Кортеж с логином и токеном.
    :param envs: Конфигурация окружения.
    :param spend_db: Объект доступа к БД.
    :yields: Экземпляр CategoryDTO.
    """
    token = login[2]
    session = BaseSession(envs.api_url)
    api = CategoriesApiClient(session, token)
    category_name = "TestCat"
    current_categories = api.get_all_categories()
    category_obj = next((c for c in current_categories if c.name == category_name), None)
    if not category_obj:
        category_obj = api.add_category(category_name)
    yield category_obj
    spend_db.delete_category_by_id(category_obj.id)

@pytest.fixture
def add_and_cleanup_category(spend_db) -> Generator[Any, Any, None]:
    """
    Фикстура-менеджер для отслеживания и последующего удаления тестовых категорий из БД.

    :param spend_db: Объект доступа к БД.
    :return: Внутренняя функция для добавления категории в список на удаление.
    После завершения теста удаляет все отмеченные категории.
    """
    created = []
    def _add_category(name):
        if isinstance(name, list):
            created.extend(name)
        else:
            created.append(name)
    yield _add_category
    if created:
        spend_db.delete_categories_by_names(created)