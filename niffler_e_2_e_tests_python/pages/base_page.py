import allure
from playwright.sync_api import Page, Response

from niffler_e_2_e_tests_python.navigation.navbar import Navbar


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.navbar = Navbar(page)

    def visit(self, url: str) -> Response | None:
        with allure.step(f'Opening the url "{url}"'):
            return self.page.goto(url, wait_until='load')

    def reload(self) -> Response | None:
        with allure.step(f'Reloading page with url "{self.page.url}"'):
            return self.page.reload(wait_until='load')

    def get_current_url(self) -> str:
        url = self.page.url
        with allure.step(f'Getting current url = "{url}"'):
            return url

    def press_enter(self):
        self.page.keyboard.press('Enter')