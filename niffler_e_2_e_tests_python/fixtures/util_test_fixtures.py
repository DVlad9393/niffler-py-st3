import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from niffler_e_2_e_tests_python.data.data_test import DataTest
from niffler_e_2_e_tests_python.databases.spend_db import SpendDB
from niffler_e_2_e_tests_python.models.category import CategoryDTO
from niffler_e_2_e_tests_python.models.spend import SpendAdd, SpendDTO
from niffler_e_2_e_tests_python.utils.api_clients import (
    CategoriesApiClient,
    SpendApiClient,
)
from niffler_e_2_e_tests_python.utils.base_session import BaseSession

TEST_CATEGORY_NAME = DataTest.TEST_CATEGORY_NAME.value
CATEGORY_NAME = DataTest.CATEGORY_NAME.value


@pytest.fixture
def add_spending(
    spend_api, category, envs, api_test_user
) -> Callable[[Any, int, Any, str], SpendDTO]:
    """Фикстура-обёртка для добавления новой траты.

    :param spend_api: API клиент SpendApiClient.
    :param category: Объект категории.
    :param envs: данные окружения.
    :return: Внутренняя функция _add_spending для добавления траты через API.
    """

    def _add_spending(description, amount=100, category_name=None, currency="RUB"):
        username = api_test_user.username

        category_obj = category
        if category_name:
            all_categories = spend_api.session.get(
                "/api/categories/all", headers=spend_api.headers
            ).json()
            match = next(
                (c for c in all_categories if c["name"] == category_name), None
            )
            if not match:
                match = spend_api.session.post(
                    "/api/categories/add",
                    json={"name": category_name, "username": username},
                    headers=spend_api.headers,
                ).json()
            category_obj = CategoryDTO(**match)
        spend = SpendAdd(
            id=str(uuid.uuid4()),
            spendDate=(datetime.now(UTC) - timedelta(minutes=1)),
            category=category_obj,
            currency=currency,
            amount=amount,
            description=description,
        )

        return spend_api.add_spending(spend, category_obj, username)

    return _add_spending


@pytest.fixture
def spendings_manager(api_auth_token, envs) -> Generator[Any, Any]:
    """Фикстура-менеджер для создания и очистки трат. После завершения теста удаляет созданные траты.

    :param api_auth_token: Токен.
    :param envs: Конфигурация окружения.
    :yields: Кортеж (spend_api, created_spendings).
    """
    token = api_auth_token
    session = BaseSession(envs.api_url)
    spend_api = SpendApiClient(session, token)
    created_spendings = []

    yield spend_api, created_spendings

    spends = spend_api.get_all_spends()
    ids_to_delete = [s.id for s in spends if s.description in created_spendings]
    if ids_to_delete:
        spend_api.delete_spending(ids_to_delete)
    session.close()


@pytest.fixture()
def category(api_auth_token, envs, spend_db) -> Generator[CategoryDTO, Any]:
    """Фикстура для получения/создания тестовой категории (по умолчанию 'TestCat').
    После завершения теста удаляет созданную категорию из БД.

    :param api_auth_token: Токен.
    :param envs: Конфигурация окружения.
    :param spend_db: Объект доступа к БД.
    :yields: Экземпляр CategoryDTO.
    """

    token = api_auth_token
    session = BaseSession(envs.api_url)
    api = CategoriesApiClient(session, token)
    category_name = "TestCat"
    current_categories = api.get_all_categories()
    category_obj = next(
        (c for c in current_categories if c.name == category_name), None
    )
    if not category_obj:
        category_obj = api.add_category(category_name)
    yield category_obj
    spend_db.delete_category_by_id(category_obj.id)


@pytest.fixture
def add_and_cleanup_category(spend_db) -> Generator[Any, Any]:
    """Фикстура-менеджер для отслеживания и последующего удаления тестовых категорий из БД.

    :param spend_db: Объект доступа к БД.
    :return: Внутренняя функция для добавления категории в список на удаление.
    После завершения теста удаляет все отмеченные категории.
    """
    created = []

    def _add_category(name):
        if isinstance(name, list):
            created.extend(name)
        else:
            created.append(name)

    yield _add_category
    if created:
        spend_db.delete_categories_by_names(created)


@pytest.fixture
def create_test_category_api(
    category_api: CategoriesApiClient, spend_db: SpendDB
) -> Generator[CategoryDTO, Any]:
    """Создаёт тестовую категорию и удаляет после теста."""
    try:
        category = category_api.add_category(CATEGORY_NAME)
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 409:
            spend_db.delete_category_by_name(CATEGORY_NAME)
            category = category_api.add_category(CATEGORY_NAME)

    yield category

    categories = category_api.get_all_categories()
    for c in categories:
        if c.id == category.id:
            spend_db.delete_category_by_id(c.id)


@pytest.fixture
def create_test_spend_api(
    spend_api: SpendApiClient,
    create_test_category_api: CategoryDTO,
    envs,
    api_test_user,
) -> Generator[Any, Any]:
    """Создаёт тестовую трату и удаляет после теста."""
    spend = SpendAdd(
        id=None,
        spendDate=(datetime.now(UTC) - timedelta(minutes=1)),
        category=create_test_category_api,
        currency="RUB",
        amount=150,
        description="Тестовая трата",
    )
    spend_dto = spend_api.add_spending(
        spend, create_test_category_api, api_test_user.username
    )
    yield spend_dto.id
    spend_api.delete_spending([spend_dto.id])
