
import pytest

from ..pages.main_page import MainPage
from ..pages.new_spending_page import NewSpendingPage
from dotenv import load_dotenv
import os
from niffler_e_2_e_tests_python.utils.base_session import BaseSession
from niffler_e_2_e_tests_python.utils.utils import SpendApiClient, CategoriesApiClient, UserApiClient
from datetime import datetime, timezone


load_dotenv()
base_auth_url = os.getenv("BASE_AUTH_URL")
base_url = os.getenv("BASE_URL")
api_url = os.getenv("API_URL")

@pytest.mark.spending
def test_add_spending_ui(main_page: MainPage, new_spending_page: NewSpendingPage, login):
    main_page.history_of_spending_title.should_be_visible()
    main_page.no_spending_text.should_be_visible()
    main_page.navbar.open_new_spending_page()
    new_spending_page.amount_input.fill("300")
    new_spending_page.currency_select.click()
    new_spending_page.currency_option_rub.click()
    new_spending_page.category_input.fill("Groceries")
    new_spending_page.date_input.fill("06/22/2025")
    new_spending_page.description_input.fill("Buy milk")
    new_spending_page.add_button.click()
    main_page.first_row_description.should_have_text("Buy milk")

    api_url = os.getenv("API_URL")
    token = login[2]
    session = BaseSession(api_url)
    spend_api = SpendApiClient(session, token)

    response = spend_api.get_all_spends()
    assert response.status_code == 200
    spends = response.json()

    ids_to_delete = [str(s["id"]) for s in spends if s.get("description") == "Buy milk"]
    if ids_to_delete:
        spend_api.delete_spending(ids_to_delete)
    session.close()

@pytest.mark.spending
def test_cancel_spending_form(main_page: MainPage, new_spending_page: NewSpendingPage, login):
    main_page.history_of_spending_title.should_be_visible()
    main_page.no_spending_text.should_be_visible()
    main_page.navbar.open_new_spending_page()
    new_spending_page.amount_input.fill("123")
    new_spending_page.cancel_button.click()
    new_spending_page.title.should_not_be_visible()
    main_page.history_of_spending_title.should_be_visible()

@pytest.mark.spending
def test_spending_form_without_amount(main_page: MainPage, new_spending_page: NewSpendingPage, login):
    main_page.history_of_spending_title.should_be_visible()
    main_page.no_spending_text.should_be_visible()
    main_page.navbar.open_new_spending_page()
    new_spending_page.amount_input.fill("")
    new_spending_page.add_button.click()
    new_spending_page.error_amount_message.should_be_visible()

@pytest.mark.spending
def test_statistics_visible(main_page: MainPage, login):
    main_page.history_of_spending_title.should_be_visible()
    main_page.no_spending_text.should_be_visible()
    main_page.statistics_block.should_be_visible()
    main_page.statistics_title.should_have_text("Statistics")
    main_page.statistics_canvas.should_be_visible()


import pytest
from datetime import datetime, timezone

@pytest.mark.spending
def test_spending_appears_in_history(main_page: MainPage, login):
    token = login[2]
    session = BaseSession(api_url)
    spend_api = SpendApiClient(session, token)

    # Формируем актуальную дату в нужном формате
    spend_date = datetime(2025, 6, 22, 23, 37, 13, 695000, tzinfo=timezone.utc).isoformat()

    spend = {
        "spendDate": spend_date,
        "category": {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # можно сгенерировать uuid.uuid4() если важно уникально
            "name": "API Category",
            "username": login[0],  # имя пользователя из фикстуры
            "archived": False
        },
        "currency": "RUB",
        "amount": 432,
        "description": "SpendingFromAPI",
        "username": login[0]
    }

    created = spend_api.add_spending(spend).json()
    main_page.reload()

    main_page.first_row_description.should_have_text("SpendingFromAPI")

    spend_api.delete_spending([str(created["id"])])
    session.close()

@pytest.mark.spending
def test_delete_spending_ui(main_page: MainPage, login):
    token = login[2]
    session = BaseSession(api_url)
    spend_api = SpendApiClient(session, token)

    spend_date = datetime(2025, 6, 22, 23, 37, 13, 695000, tzinfo=timezone.utc).isoformat()
    spend = {
        "spendDate": spend_date,
        "category": {
            "id": "cd9d5ba0-82cf-456a-b2f2-4e95b9f130b9",  # можешь генерировать uuid
            "name": "DelCat",
            "username": login[0],
            "archived": False
        },
        "currency": "RUB",
        "amount": 99,
        "description": "DelThis",
        "username": login[0]
    }
    created = spend_api.add_spending(spend).json()
    main_page.reload()
    main_page.first_row_description.should_have_text("DelThis")
    main_page.first_row_checkbox.click()
    main_page.first_row_checkbox.should_be_checked()
    main_page.delete_button.click()
    main_page.delete_button_dialog.click()
    main_page.no_spending_text.should_be_visible()
    # Clean-up на всякий случай (если в UI не удалилось)
    spend_api.delete_spending([str(created["id"])])
    session.close()

@pytest.mark.spending
def test_search_spending_by_description(main_page: MainPage, login):
    token = login[2]
    session = BaseSession(api_url)
    spend_api = SpendApiClient(session, token)

    spend_date = datetime(2025, 6, 22, 23, 37, 13, 695000, tzinfo=timezone.utc).isoformat()
    spend = {
        "spendDate": spend_date,
        "category": {
            "id": "42fcd137-6bb7-4a93-8938-b3267d6e070e",
            "name": "Test",
            "username": login[0],
            "archived": False
        },
        "currency": "RUB",
        "amount": 150,
        "description": "UniqueDesc123",
        "username": login[0]
    }
    created = spend_api.add_spending(spend).json()
    main_page.reload()
    main_page.search_button.should_be_visible()
    main_page.search_input.fill("UniqueDesc123")
    main_page.first_row_description.should_have_text("UniqueDesc123")
    spend_api.delete_spending([str(created["id"])])
    session.close()