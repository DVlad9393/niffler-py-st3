import time
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest
from faker import Faker

from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.utils.auth_client import AuthClient


@dataclass
class TestUser:
    username: str
    password: str
    token: str


fake = Faker()


@pytest.fixture(scope="function")
def api_test_user(envs: Envs, create_test_data, db_client) -> Generator[TestUser, Any]:
    """Создаёт нового пользователя под КАЖДЫЙ тест и удаляет его после выполнения.
    Гарантирует уникальность username и корректную работу при параллельных запусках.
    """
    username = f"{create_test_data[0]}_{fake.uuid4()[:8]}"
    password = fake.password(
        length=12, special_chars=True, digits=True, upper_case=True
    )

    auth = AuthClient(envs)

    for _ in range(3):
        reg_resp = auth.registration(username, password, envs)
        if reg_resp.status_code in (200, 201, 302):
            break
        time.sleep(1)
    else:
        raise AssertionError(
            f"Registration failed after retries: {reg_resp.status_code}"
        )

    token = auth.get_token(username, password)
    assert token, f"Token was not issued for user {username}"

    user = TestUser(username=username, password=password, token=token)

    yield user

    db_client.delete_user_by_username_from_users_and_friendship(username)


@pytest.fixture(scope="function")
def two_api_users(
    envs, db_client, create_test_data
) -> Generator[tuple[TestUser, TestUser], Any]:
    """Создаёт двух независимых пользователей."""
    auth = AuthClient(envs)
    users = []

    for _i in range(2):
        username = f"{create_test_data[0]}_{fake.uuid4()[:8]}"
        password = fake.password(
            length=12, special_chars=True, digits=True, upper_case=True
        )

        for _ in range(3):
            reg_resp = auth.registration(username, password, envs)
            if reg_resp.status_code in (200, 201, 302):
                break
            time.sleep(1)
        else:
            raise AssertionError(f"Registration failed for {username}")

        token = auth.get_token(username, password)
        assert token, f"Token not issued for user {username}"
        users.append(TestUser(username=username, password=password, token=token))

    yield tuple(users)

    for u in users:
        db_client.delete_user_by_username_from_users_and_friendship(u.username)


@pytest.fixture(scope="function")
def api_auth_token(api_test_user: TestUser, envs: Envs) -> str:
    """Фикстура для получения access_token для API-тестов (через AuthClient, минуя браузер)."""
    client = AuthClient(envs)
    return client.get_token(api_test_user.username, api_test_user.password)
