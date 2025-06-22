from dotenv import load_dotenv
import os
import pytest

load_dotenv()
base_auth_url = os.getenv("BASE_AUTH_URL")
base_url = os.getenv("BASE_URL")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

if not username or not password:
    raise RuntimeError("Set USERNAME and PASSWORD in your .env file")


from typing import Any, Generator

import allure
import sys
import os

from niffler_e_2_e_tests_python.pages.login_page import LoginPage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from playwright.sync_api import Page, sync_playwright

from niffler_e_2_e_tests_python.pages.main_page import MainPage
from niffler_e_2_e_tests_python.pages.new_spending_page import NewSpendingPage

from faker import Faker

fake = Faker()


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
def create_user(login_page: LoginPage, create_test_data) -> tuple[str, str]:
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
def login(login_page: LoginPage, main_page: MainPage) -> tuple[str, str, str]:
    login_page.visit(base_auth_url)
    login_page.input_username.fill(username)
    login_page.input_password.fill(password)
    token = login_page.login_button.click(intercept_header=True)
    main_page.history_of_spending_title.should_be_visible()
    return username, password, token