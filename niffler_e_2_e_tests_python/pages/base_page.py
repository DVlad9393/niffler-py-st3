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

    def get_auth_token_from_request(self, url_filter: str = "/api/session/current", timeout_ms: int = 2000) -> str | None:
        """
        Перехватывает токен авторизации из заголовка Authorization в запросе к заданному URL (по умолчанию '/api/session/current').
        Возвращает строку токена или None, если не найден.
        """
        token_holder = {"token": None}

        def handle_request(request):
            if url_filter in request.url:
                auth_header = request.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token_holder["token"] = auth_header.split("Bearer ")[1]

        self.page.on("request", handle_request)
        # Важно: здесь должен быть action, который вызовет нужный запрос, например self.page.goto(...) или клик, либо этот метод вызывается после действия
        self.page.wait_for_timeout(timeout_ms)
        self.page.off("request", handle_request)
        return token_holder["token"]