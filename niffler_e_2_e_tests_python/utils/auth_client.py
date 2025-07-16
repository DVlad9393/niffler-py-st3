import base64
import hashlib
import os
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import allure
from requests import Response, Session

from niffler_e_2_e_tests_python.models.config import Envs


class AuthSession(Session):
    """Кастомная сессия на основе requests.Session,
    автоматически обновляет куки при переходах и сохраняет auth code из Location.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.code: str | None = None

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

    def __init__(self, env: Envs) -> None:
        """:param env: Конфиг с параметрами окружения"""
        self.session: AuthSession = AuthSession()
        self.domain_url: str = env.auth_url
        self.code_verifier: str = base64.urlsafe_b64encode(os.urandom(32)).decode(
            "utf-8"
        )
        self.code_verifier = re.sub(r"[^a-zA-Z0-9]+", "", self.code_verifier)

        code_challenge_bytes = hashlib.sha256(
            self.code_verifier.encode("utf-8")
        ).digest()
        self.code_challenge: str = (
            base64.urlsafe_b64encode(code_challenge_bytes)
            .decode("utf-8")
            .replace("=", "")
        )

        self._basic_token: str = base64.b64encode(
            env.auth_secret.encode("utf-8")
        ).decode("utf-8")
        self.authorization_basic: dict[str, str] = {
            "Authorization": f"Basic {self._basic_token}"
        }
        self.token: str | None = None

    def auth(self, username: str, password: str) -> str | None:
        """Проходит цепочку OAuth2 авторизации и возвращает access_token.

        :param username: Имя пользователя
        :param password: Пароль пользователя
        :return: Строка access_token или None
        """
        with allure.step(f"Get auth token for user:{username}"):
            session = AuthSession()

            session.get(
                url=f"{self.domain_url}/oauth2/authorize",
                params={
                    "response_type": "code",
                    "client_id": "client",
                    "scope": "openid",
                    "redirect_uri": "http://frontend.niffler.dc/authorized",
                    "code_challenge": self.code_challenge,
                    "code_challenge_method": "S256",
                },
                allow_redirects=True,
            )

            session.post(
                url=f"{self.domain_url}/login",
                data={
                    "username": username,
                    "password": password,
                    "_csrf": session.cookies.get("XSRF-TOKEN"),
                },
                allow_redirects=True,
            )

            token_response = session.post(
                url=f"{self.domain_url}/oauth2/token",
                data={
                    "code": session.code,
                    "redirect_uri": "http://frontend.niffler.dc/authorized",
                    "code_verifier": self.code_verifier,
                    "grant_type": "authorization_code",
                    "client_id": "client",
                },
            )

            self.token = token_response.json().get("access_token", None)
            return self.token
