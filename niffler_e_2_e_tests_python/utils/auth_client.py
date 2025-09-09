import base64
from typing import Any
from urllib.parse import parse_qs, urlparse

import allure
import pkce
from requests import Response, Session

from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.models.oauth import OAuthRequest
from niffler_e_2_e_tests_python.utils.allure_helpers import allure_attach_request


class AuthSession(Session):
    """Кастомная сессия на основе requests.Session,
    автоматически обновляет куки при переходах и сохраняет auth code из Location.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Прокидываем base_url - url авторизации из энвов
        code - код авторизации из redirect_uri.
        """
        super().__init__()
        self.code: str | None = None
        self.base_url = kwargs.pop("base_url", "")

    @allure_attach_request
    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        """Выполняет HTTP-запрос, обновляет куки и ищет code в редиректах.

        :param method: HTTP-метод (GET, POST и т.д.)
        :param url: URL запроса
        :param kwargs: дополнительные параметры для requests
        :return: объект Response
        """
        with allure.step(f"Request: {method} {url}"):
            response = super().request(method, url, **kwargs)
            for r in response.history:
                cookies = r.cookies.get_dict()
                self.cookies.update(cookies)
                code = parse_qs(urlparse(r.headers.get("Location", "")).query).get(
                    "code", None
                )
                if code:
                    self.code = code[0]
            return response


class AuthClient:
    """Клиент для аутентификации пользователя через OAuth2 с поддержкой PKCE."""

    session: AuthSession
    base_url: str

    def __init__(self, env: Envs) -> None:
        """:param env: Конфиг с параметрами окружения"""
        self.session: AuthSession = AuthSession(base_url=env.auth_url)
        self.redirect_uri = env.frontend_url + "/authorized"
        # этот код написан самостоятельно и заменен на целевую pkce

        # self.code_verifier: str = base64.urlsafe_b64encode(os.urandom(32)).decode(
        #     "utf-8"
        # )
        # self.code_verifier = re.sub(r"[^a-zA-Z0-9]+", "", self.code_verifier)
        #
        # code_challenge_bytes = hashlib.sha256(
        #     self.code_verifier.encode("utf-8")
        # ).digest()
        # self.code_challenge: str = (
        #     base64.urlsafe_b64encode(code_challenge_bytes)
        #     .decode("utf-8")
        #     .replace("=", "")
        # )
        self.code_verifier, self.code_challenge = pkce.generate_pkce_pair()

        self._basic_token: str = base64.b64encode(
            env.auth_secret.encode("utf-8")
        ).decode("utf-8")
        self.authorization_basic: dict[str, str] = {
            "Authorization": f"Basic {self._basic_token}"
        }
        self.token: str | None = None

    def get_token(self, username, password):
        """Возвращает token oauth для авторизации пользователя с username и password
        1. Получаем jsessionid и xsrf-token куку в сессию.
        2. Получаем code из redirect по xsrf-token'у.
        3. Получаем access_token.
        """
        self.session.get(
            url=f"{self.session.base_url}/oauth2/authorize",
            params=OAuthRequest(
                redirect_uri=self.redirect_uri, code_challenge=self.code_challenge
            ).model_dump(),
            allow_redirects=True,
        )

        self.session.post(
            url=f"{self.session.base_url}/login",
            data={
                "username": username,
                "password": password,
                "_csrf": self.session.cookies.get("XSRF-TOKEN"),
            },
            allow_redirects=True,
        )

        token_response = self.session.post(
            url=f"{self.session.base_url}/oauth2/token",
            data={
                "code": self.session.code,
                "redirect_uri": self.redirect_uri,
                "code_verifier": self.code_verifier,
                "grant_type": "authorization_code",
                "client_id": "client",
            },
        )

        self.token = token_response.json().get("access_token", None)
        return self.token

    def registration(self, username, password, envs: Envs):
        """Регистрирует пользователя через форму `/register` с использованием сессионных куки и CSRF.

        Последовательность действий:
          1) Выполняется GET-запрос к странице регистрации, чтобы инициализировать сессию
             и получить CSRF-куки (`XSRF-TOKEN`). Разрешены переадресации.
          2) Выполняется POST-запрос на тот же URL с формой регистрации:
             передаются поля `username`, `password`, `passwordSubmit` (повтор пароля)
             и `_csrf`, извлечённый из куки `XSRF-TOKEN`. Разрешены переадресации.

        Примечания:
          • Метод использует общий сессионный клиент (`self.session`), поэтому куки
            и заголовки, установленные сервером, сохраняются между запросами.
          • Значение `redirect_uri` фиксировано и передаётся как query-параметр первого запроса.
          • Проверку успешности операции оставляет вызывающей стороне (например, по статус-коду
            или содержимому ответа).

        :param username: Имя пользователя, которое нужно зарегистрировать.
        :param password: Пароль пользователя; также используется как повторное значение `passwordSubmit`.
        :param envs: Объект окружения с базовым адресом сервиса авторизации (`auth_url`).
        :return: HTTP-ответ клиента после POST-запроса регистрации (с учётом переадресаций).
        :raises: Сетевые и клиентские исключения при недоступности сервиса или сбое запроса.
        """
        self.session.get(
            url=f"{envs.auth_url}/register",
            params={
                "redirect_uri": "http://auth.niffler.dc:9000/register",
            },
            allow_redirects=True,
        )

        result = self.session.post(
            url=f"{envs.auth_url}/register",
            data={
                "username": username,
                "password": password,
                "passwordSubmit": password,
                "_csrf": self.session.cookies.get("XSRF-TOKEN"),
            },
            allow_redirects=True,
        )
        return result
