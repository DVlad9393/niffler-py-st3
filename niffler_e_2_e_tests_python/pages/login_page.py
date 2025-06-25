import os

import allure
from playwright.sync_api import Page

from niffler_e_2_e_tests_python.page_factory.button import Button
from niffler_e_2_e_tests_python.page_factory.title import Title
from niffler_e_2_e_tests_python.page_factory.input import Input
from niffler_e_2_e_tests_python.page_factory.link import Link
from niffler_e_2_e_tests_python.page_factory.image import Image
from niffler_e_2_e_tests_python.page_factory.text import Text
from niffler_e_2_e_tests_python.pages.base_page import BasePage

from dotenv import load_dotenv

load_dotenv()
base_auth_url = os.getenv("BASE_AUTH_URL")
base_url = os.getenv("BASE_URL")

class LoginPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

        self.login_title = Title(
            page, locator='h1[class="header"]', name='Login title')

        self.loogin_image = Image(page, locator='div[class="main__hero"]', name='Logo')

        self.login_button = Button(
            page, locator='button[type="submit"]', name='Login button')

        self.sign_up_title = Title(
            page, locator='h1[class="header"]', name='Sign up title')

        self.info_have_an_account_text = Text(page, locator='p[class="header__additional"]', name='Info have an account text')
        self.log_in_button = Link(page, locator='p[class="header__additional"] a[class="form__link"]', name='Log in link')

        self.sign_up_button = Button(
            page, locator='button[type="submit"]', name='Sign up button'
        )
        self.sign_in_link = Link(
            page, locator='a[href="http://frontend.niffler.dc/main"]', name='Sign up link')

        self.create_new_account_button = Button(
            page, locator='a[href="/register"]', name='Register button')

        self.input_username = Input(
            page, locator='input[name="username"]', name='Input username')

        self.input_password = Input(
            page, locator='input[name="password"]', name='Input password')

        self.input_password_text = Text(page, locator='div[contenteditable="plaintext-only"]', name='Input password')

        self.input_password_hide_text_image = Image(page, locator='button[class="form__password-button form__password-button_active"][id="passwordBtn"]', name="Input password hide text image")
        self.input_password_show_text_image = Image(page, locator='button[class="form__password-button"][id="passwordBtn"]',
                                                    name="Input password show text image")


        self.input_submit_password_hide_text_image = Image(page, locator='button[class="form__password-button"][id="passwordSubmitBtn"]', name="Input password hide text image")
        self.input_submit_password_show_text_image = Image(page, locator='button[class="form__password-button form__password-button_active"][id="passwordSubmitBtn"]',
                                                    name="Input password show text image")
        self.input_submit_password = Input(page, locator='input[placeholder="Submit your password"]', name='Input password')
        self.congratulations_register_text = Text(page, locator='//p[contains(text(), "Congratulations!")]', name='Congratulations register text')
        self.incorrect_login_or_password_text = Text(page, locator='//p[contains(text(), "Неверные учетные данные пользователя")]', name='Incorrect login or password text')

    def login(self, username: str, password: str) -> None:
        with allure.step(f'Logging in: {username}'):
            self.input_username.fill(username)
            self.input_password.fill(password)
            self.login_button.click()

    def create_new_account(self, username: str, password: str) -> None:
        with allure.step(f'Creating new account: {username}'):
            username = username
            password = password
            self.visit(base_auth_url)
            self.create_new_account_button.click()
            self.info_have_an_account_text.should_be_visible()
            self.log_in_button.should_be_enabled()
            self.input_username.fill(username)
            self.input_password.fill(password)
            self.input_submit_password.fill(password)
            self.sign_up_button.click()
            self.congratulations_register_text.should_be_visible()
            self.sign_in_link.click()
            self.login_title.should_be_visible()