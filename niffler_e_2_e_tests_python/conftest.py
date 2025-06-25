from dotenv import load_dotenv
import os
import pytest

from typing import Any, Generator

import allure
import sys
import uuid
from niffler_e_2_e_tests_python.pages.login_page import LoginPage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from playwright.sync_api import Page, sync_playwright

from niffler_e_2_e_tests_python.pages.main_page import MainPage
from niffler_e_2_e_tests_python.pages.new_spending_page import NewSpendingPage
from datetime import datetime, timezone
from niffler_e_2_e_tests_python.utils.base_session import BaseSession
from niffler_e_2_e_tests_python.utils.utils import SpendApiClient

from faker import Faker

fake = Faker()

@pytest.fixture(scope='session', autouse=True)
def envs():
    load_dotenv()

@pytest.fixture(scope='session')
def base_auth_url(envs):
    return os.getenv("BASE_AUTH_URL")

@pytest.fixture(scope='session')
def base_url(envs):
    return os.getenv("BASE_URL")

@pytest.fixture(scope='session')
def api_url(envs):
    return os.getenv("API_URL")

@pytest.fixture(scope='session')
def username(envs):
    return os.getenv("USERNAME")

@pytest.fixture(scope='session')
def password(envs):
    return os.getenv("PASSWORD")

@pytest.fixture(scope='session')
def base_error_url(envs):
    return os.getenv("BASE_ERROR_URL")


@pytest.fixture(scope='function', params=['chromium'])
def browser_page(request) -> Generator[Any, Any, None]:
    '''
    :params browser_name: 'chromium', 'firefox', 'webkit'
    '''
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
    return MainPage(browser_page)

@pytest.fixture(scope='function')
def login_page(browser_page: Page) -> LoginPage:
    return LoginPage(browser_page)

@pytest.fixture(scope='function')
def new_spending_page(browser_page: Page) -> NewSpendingPage:
    return NewSpendingPage(browser_page)

@pytest.fixture(scope='function')
def create_test_data():
    username = fake.user_name()
    password = fake.password()
    return username, password

@pytest.fixture(scope='function')
def create_user(login_page: LoginPage, create_test_data, base_auth_url) -> tuple[str, str]:
    username, password = create_test_data
    login_page.visit(base_auth_url)
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
def login(login_page: LoginPage, main_page: MainPage, base_auth_url, username, password) -> tuple[str, str, str]:
    login_page.visit(base_auth_url)
    login_page.input_username.fill(username)
    login_page.input_password.fill(password)
    token = login_page.login_button.click(intercept_header=True)
    main_page.history_of_spending_title.should_be_visible()
    return username, password, token

@pytest.fixture
def spend_api(login, api_url):
    token = login[2]
    session = BaseSession(api_url)
    api = SpendApiClient(session, token)
    yield api
    session.close()

@pytest.fixture
def add_spending(spend_api, login):
    def _add_spending(description, amount=100, category_name="TestCat", currency="RUB"):
        spend_date = datetime.now(timezone.utc).isoformat()
        spend = {
            "spendDate": spend_date,
            "category": {
                "id": str(uuid.uuid4()),
                "name": category_name,
                "username": login[0],
                "archived": False
            },
            "currency": currency,
            "amount": amount,
            "description": description,
            "username": login[0]
        }
        response = spend_api.add_spending(spend)
        response.raise_for_status()
        return response.json()
    return _add_spending


@pytest.fixture
def spendings_manager(login, api_url):

    token = login[2]
    session = BaseSession(api_url)
    spend_api = SpendApiClient(session, token)
    created_spendings = []

    yield spend_api, created_spendings

    response = spend_api.get_all_spends()
    if response.status_code == 200:
        spends = response.json()
        ids_to_delete = [
            str(s["id"])
            for s in spends
            if s.get("description") in created_spendings
        ]
        if ids_to_delete:
            spend_api.delete_spending(ids_to_delete)
    session.close()