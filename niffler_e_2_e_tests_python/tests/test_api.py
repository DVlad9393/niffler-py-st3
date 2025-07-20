from datetime import UTC, datetime, timedelta

import allure
import pytest

from niffler_e_2_e_tests_python.data.data_test import DataTest
from niffler_e_2_e_tests_python.databases.spend_db import SpendDB
from niffler_e_2_e_tests_python.models.category import CategoryDTO
from niffler_e_2_e_tests_python.models.spend import SpendAdd
from niffler_e_2_e_tests_python.utils.api_clients import (
    CategoriesApiClient,
    SpendApiClient,
)

TEST_CATEGORY_NAME = DataTest.TEST_CATEGORY_NAME.value
CATEGORY_NAME = DataTest.CATEGORY_NAME.value
ALT_CATEGORY_NAME = DataTest.ALT_CATEGORY_NAME.value


@allure.feature("Spending")
@allure.story("Spending category")
@pytest.mark.api
def test_add_category_api(category_api: CategoriesApiClient, spend_db: SpendDB):
    """Проверка успешного создания новой категории."""
    spend_db.delete_category_by_name(TEST_CATEGORY_NAME)
    category = category_api.add_category(TEST_CATEGORY_NAME)
    all_categories = category_api.get_all_categories()
    result_category = next(
        (c for c in all_categories if c.name == TEST_CATEGORY_NAME), None
    )
    assert category.name == TEST_CATEGORY_NAME
    assert result_category.id == category.id
    if spend_db.get_category_by_name(TEST_CATEGORY_NAME):
        spend_db.delete_category_by_name(TEST_CATEGORY_NAME)


@allure.feature("Spending")
@allure.story("Spending category")
@pytest.mark.api
def test_get_all_categories_api(
    category_api: CategoriesApiClient, create_test_category_api: CategoryDTO
):
    """Проверка получения всех категорий, включая только что добавленную."""
    categories = category_api.get_all_categories()
    assert any(c.id == create_test_category_api.id for c in categories)


@allure.feature("Spending")
@allure.story("Spending category")
@pytest.mark.api
def test_update_category_api(
    category_api: CategoriesApiClient,
    create_test_category_api: CategoryDTO,
    spend_db: SpendDB,
):
    """Проверка обновления имени категории."""
    updated = category_api.update_category(
        create_test_category_api.id, ALT_CATEGORY_NAME, archived=False
    )
    categories = category_api.get_all_categories()
    assert updated.name == ALT_CATEGORY_NAME
    assert any(c.name == updated.name for c in categories)


@allure.feature("Spending")
@allure.story("Spending CRUD")
@pytest.mark.api
def test_add_spending_api(
    spend_api: SpendApiClient, create_test_category_api: CategoryDTO, envs
):
    """Проверка добавления траты."""
    spend = SpendAdd(
        id=None,
        spendDate=(datetime.now(UTC) - timedelta(minutes=1)),
        category=create_test_category_api,
        currency="RUB",
        amount=123,
        description="API-тест",
    )
    spend_dto = spend_api.add_spending(spend, create_test_category_api, envs.username)
    result = spend_api.get_spending_by_id(spend_dto.id)
    assert spend_dto.description == "API-тест"
    assert result.id == spend_dto.id
    spend_api.delete_spending([spend_dto.id])


@allure.feature("Spending")
@allure.story("Spending CRUD")
@pytest.mark.api
def test_get_all_spends_api(spend_api: SpendApiClient, create_test_spend_api: str):
    """Проверка получения всех трат, включая добавленную."""
    spends = spend_api.get_all_spends()
    assert any(s.id == create_test_spend_api for s in spends)


@allure.feature("Spending")
@allure.story("Spending CRUD")
@pytest.mark.api
def test_delete_spending_api(
    spend_api: SpendApiClient, create_test_category_api: CategoryDTO, envs
):
    """Проверка удаления траты."""
    spend = SpendAdd(
        id=None,
        spendDate=(datetime.now(UTC) - timedelta(minutes=1)),
        category=create_test_category_api,
        currency="RUB",
        amount=150,
        description="Тестовая трата",
    )
    spend_dto = spend_api.add_spending(spend, create_test_category_api, envs.username)
    resp = spend_api.delete_spending([spend_dto.id])
    db_spends = spend_api.get_all_spends()
    assert resp.status_code == 200
    assert not any(s.id == spend_dto.id for s in db_spends)


@allure.feature("Spending")
@allure.story("Spending filters")
@pytest.mark.api
def test_filter_spending_by_currency_api(
    spend_api: SpendApiClient, create_test_spend_api: str
):
    """Проверка фильтра по валюте."""
    spends = spend_api.get_all_spends(filter_currency="RUB")
    assert any(s.id == create_test_spend_api for s in spends)


@allure.feature("Spending")
@allure.story("Spending negative")
@pytest.mark.api
def test_add_spending_invalid_currency_api(
    spend_api: SpendApiClient, create_test_category_api: CategoryDTO, envs
):
    """Проверка ошибки при добавлении траты с невалидной валютой."""
    spend = SpendAdd(
        id=None,
        spendDate=(datetime.now(UTC) - timedelta(minutes=1)),
        category=create_test_category_api,
        currency="FAKE",
        amount=50,
        description="Bad currency",
    )
    resp = spend_api.add_invalid_spending(
        spend, create_test_category_api, envs.username
    )
    result = spend_api.get_not_exists_spending_by_id(spend.id)
    assert resp.status_code == 400
    assert result.status_code == 404


@allure.feature("Spending")
@allure.story("Spending negative")
@pytest.mark.api
def test_delete_spending_invalid_id_api(spend_api: SpendApiClient):
    """Проверка удаления несуществующей траты (ожидается ошибка или 4xx)."""
    resp = spend_api.delete_not_exists_spending(["non-existent-id"])
    assert resp.status_code == 500


@allure.feature("Spending")
@allure.story("Spending negative")
@pytest.mark.api
def test_add_duplicate_category_api(
    category_api: CategoriesApiClient, create_test_category_api: CategoryDTO
):
    """Проверка добавления дублирующейся категории (ожидается ошибка 4xx)."""
    resp = category_api.add_duplicate_category(create_test_category_api.name)
    categories = category_api.get_all_categories()
    categories_count = len(
        [(c.name == create_test_category_api.name for c in categories)]
    )
    assert resp.status_code == 409
    assert categories_count == 1
