from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest

from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.utils.auth_client import AuthClient


@dataclass
class TestUser:
    username: str
    password: str
    token: str


@pytest.fixture(scope="function")
def api_test_user(envs: Envs, create_test_data, db_client) -> Generator[TestUser, Any]:
    """Создаёт нового пользователя под КАЖДЫЙ тест, проходит регистрацию и логин (PKCE),
    возвращает username/password/token. Подходит для параллельных прогонов (xdist).

    После завершения теста гарантированно удаляет пользователя из базы данных,
    чтобы не накапливались «мусорные» учётные записи.

    :param envs: Конфигурация окружения (URLs, секреты, адрес БД и т.п.).
    :param create_test_data: Фикстура, генерирующая пару (username, password).
    :param db_client: Клиент доступа к БД пользователей (`UsersDb`).
    :yield: Объект TestUser с полями username, password, token.
    """
    username, password = create_test_data

    auth = AuthClient(envs)
    reg_resp = auth.registration(username, password, envs)
    assert reg_resp.status_code in (
        200,
        201,
        302,
    ), f"Registration failed: {reg_resp.status_code}"

    token = auth.get_token(username, password)
    assert token, "Token was not issued"

    user = TestUser(username=username, password=password, token=token)

    yield user
    db_client.delete_user_by_username(username)


@pytest.fixture(scope="function")
def api_auth_token(api_test_user: TestUser, envs: Envs) -> str:
    """Фикстура для получения access_token для API-тестов (через AuthClient, минуя браузер)."""
    client = AuthClient(envs)
    return client.get_token(api_test_user.username, api_test_user.password)
