import allure
from playwright.sync_api import Page, Response

from niffler_e_2_e_tests_python.navigation.navbar import Navbar


class BasePage:
    """Базовый класс для всех страниц веб-приложения.

    Содержит общие методы для навигации, перезагрузки страницы и работы с URL.
    Каждая страница содержит экземпляр Navbar для управления навигационной панелью.

    :param page: Экземпляр Playwright Page.
    """

    def __init__(self, page: Page) -> None:
        """Инициализирует базовую страницу и навигационную панель.

        :param page: Экземпляр Playwright Page.
        """
        self.page = page
        self.navbar = Navbar(page)

    def visit(self, url: str) -> Response | None:
        """Открывает страницу по заданному URL.

        :param url: URL страницы для перехода.
        :return: Ответ загрузки страницы или None.
        """
        with allure.step(f'Opening the url "{url}"'):
            return self.page.goto(url, wait_until="load")

    def reload(self) -> Response | None:
        """Перезагружает текущую страницу.

        :return: Ответ загрузки страницы или None.
        """
        with allure.step(f'Reloading page with url "{self.page.url}"'):
            return self.page.reload(wait_until="load")

    def get_current_url(self) -> str:
        """Получает текущий URL страницы.

        :return: Текущий URL.
        """
        url = self.page.url
        with allure.step(f'Getting current url = "{url}"'):
            return url

    def press_enter(self) -> None:
        """Нажимает клавишу Enter на текущей странице.

        :return: None
        """
        with allure.step("Pressing Enter"):
            self.page.keyboard.press("Enter")
