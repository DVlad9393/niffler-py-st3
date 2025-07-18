from collections.abc import Generator
from typing import Any

import pytest

from niffler_e_2_e_tests_python.databases.spend_db import SpendDB
from niffler_e_2_e_tests_python.utils.api_clients import (
    CategoriesApiClient,
    SpendApiClient,
)
from niffler_e_2_e_tests_python.utils.base_session import BaseSession


@pytest.fixture
def spend_api(api_auth_token, envs) -> Generator[SpendApiClient, Any]:
    """Фикстура для создания API клиента SpendApiClient с авторизацией.

    :param api_auth_token: токен.
    :param envs: Конфигурация окружения.
    :yields: Экземпляр SpendApiClient.
    После завершения теста сессия закрывается.
    """
    token = api_auth_token
    session = BaseSession(envs.api_url)
    api = SpendApiClient(session, token)
    yield api
    session.close()


@pytest.fixture
def category_api(api_auth_token, envs) -> Generator[CategoriesApiClient, Any]:
    """Фикстура для создания API клиента CategoriesApiClient с авторизацией.

    :param login: Кортеж с логином и токеном.
    :param envs: Конфигурация окружения.
    :yields: Экземпляр SpendApiClient.
    После завершения теста сессия закрывается.
    """
    token = api_auth_token
    session = BaseSession(envs.api_url)
    api = CategoriesApiClient(session, token)
    yield api
    session.close()


@pytest.fixture(scope="session")
def spend_db(envs) -> SpendDB:
    """Фикстура для подключения к базе данных трат.

    :param envs: Конфигурация окружения.
    :return: Экземпляр SpendDB.
    """
    return SpendDB(envs.spend_db_url)
