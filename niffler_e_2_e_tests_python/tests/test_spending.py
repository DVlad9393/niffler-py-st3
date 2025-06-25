import pytest

from ..pages.main_page import MainPage
from ..pages.new_spending_page import NewSpendingPage
from datetime import datetime, timezone

@pytest.mark.spending
@pytest.mark.parametrize("desc,amount,currency", [
    ("Buy milk", 300, "RUB"),
    ("Taxi", 150, "USD"),
    ("Groceries", 222, "EUR"),
])
def test_add_spending_ui(main_page, new_spending_page, spend_api, desc, amount, currency, spendings_manager):
    spend_api, created_spendings = spendings_manager
    main_page.history_of_spending_title.should_be_visible()
    main_page.no_spending_text.should_be_visible()
    main_page.navbar.open_new_spending_page()
    new_spending_page.amount_input.fill(str(amount))
    new_spending_page.currency_select.click()
    new_spending_page.currency_option_rub.click()
    new_spending_page.category_input.fill("TestCat")
    new_spending_page.date_input.fill(datetime.now().strftime("%m/%d/%Y"))
    new_spending_page.description_input.fill(desc)
    new_spending_page.add_button.click()
    main_page.first_row_description.should_have_text(desc)

    created_spendings.append(desc)

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

@pytest.mark.spending
def test_spending_appears_in_history(main_page, add_spending, spend_api, spendings_manager,login):
    spend_api, created_spendings = spendings_manager
    description = "SpendingFromAPI"
    add_spending(description, 432)
    created_spendings.append(description)
    main_page.reload()
    main_page.first_row_description.should_have_text(description)

@pytest.mark.spending
def test_delete_spending_ui(main_page, add_spending, spend_api, spendings_manager, login):
    spend_api, created_spendings = spendings_manager
    description = "DelThis"
    add_spending(description, 99, "DelCat")
    created_spendings.append(description)
    main_page.reload()
    main_page.first_row_description.should_have_text(description)
    main_page.first_row_checkbox.click()
    main_page.first_row_checkbox.should_be_checked()
    main_page.delete_button.click()
    main_page.delete_button_dialog.click()
    main_page.no_spending_text.should_be_visible()

@pytest.mark.spending
def test_search_spending_by_description(main_page, add_spending, spend_api, spendings_manager, login):
    spend_api, created_spendings = spendings_manager
    description = "UniqueDesc123"
    add_spending(description, 150, "Test")
    created_spendings.append(description)
    main_page.reload()
    main_page.search_button.should_be_visible()
    main_page.search_input.fill(description)
    main_page.press_enter()
    main_page.first_row_description.should_have_text(description)

@pytest.mark.spending
def test_edit_spending_description(main_page, add_spending, new_spending_page, spend_api, spendings_manager, login):
    spend_api, created_spendings = spendings_manager
    description = "EditMe"
    add_spending(description, 100)
    created_spendings.append(description)
    main_page.reload()
    main_page.first_row_description.should_have_text(description)
    main_page.first_row_edit_button.click()
    new_desc = "EditedDesc"
    new_spending_page.description_input.fill(new_desc)
    new_spending_page.add_button.click()
    created_spendings.append(new_desc)
    main_page.first_row_description.should_have_text(new_desc)

@pytest.mark.spending
def test_filter_spending_by_category(main_page, add_spending, spend_api, spendings_manager):
    spend_api, created_spendings = spendings_manager
    description = "Car Wash"
    add_spending(description, 500, "Car")
    created_spendings.append(description)
    main_page.reload()
    main_page.search_input.fill("Car")
    main_page.press_enter()
    main_page.first_row_description.should_have_text(description)

@pytest.mark.spending
def test_spending_negative_amount(main_page, new_spending_page, spendings_manager):
    main_page.navbar.open_new_spending_page()
    new_spending_page.amount_input.fill("-10")
    new_spending_page.add_button.click()
    new_spending_page.error_amount_message.should_be_visible()

@pytest.mark.spending
def test_spending_empty_category(main_page, new_spending_page, spendings_manager):
    main_page.navbar.open_new_spending_page()
    new_spending_page.amount_input.fill("55")
    new_spending_page.category_input.fill("")
    new_spending_page.add_button.click()
    new_spending_page.error_no_category_message.should_be_visible()

@pytest.mark.spending
def test_spending_duplicate(main_page, add_spending, spend_api, spendings_manager):
    spend_api, created_spendings = spendings_manager
    desc = "DuplicateTest"
    add_spending(desc, 50)
    created_spendings.append(desc)
    add_spending(desc, 50)
    created_spendings.append(desc)
    main_page.reload()
    main_page.first_row_description.should_have_text(desc)
    main_page.second_row_description.should_have_text(desc)

@pytest.mark.spending
def test_delete_multiple_spendings(main_page, add_spending, spend_api, spendings_manager):
    spend_api, created_spendings = spendings_manager
    desc1, desc2 = "ToDel1", "ToDel2"
    add_spending(desc1, 11)
    add_spending(desc2, 12)
    created_spendings += [desc1, desc2]
    main_page.reload()
    main_page.first_row_checkbox.click()
    main_page.first_row_checkbox.should_be_checked()
    main_page.second_row_checkbox.click()
    main_page.second_row_checkbox.should_be_checked()
    main_page.delete_button.click()
    main_page.delete_button_dialog.click()
    main_page.no_spending_text.should_be_visible()

@pytest.mark.spending
def test_spending_search_no_results(main_page, add_spending, spend_api, spendings_manager):
    spend_api, created_spendings = spendings_manager
    add_spending("SomeDesc", 123)
    created_spendings.append("SomeDesc")
    main_page.reload()
    main_page.search_input.fill("DefinitelyNoSuchDesc")
    main_page.press_enter()
    main_page.no_spending_text.should_be_visible()

@pytest.mark.spending
def test_reload_persists_spendings(main_page, add_spending, spend_api, spendings_manager):
    spend_api, created_spendings = spendings_manager
    desc = "ReloadPersist"
    add_spending(desc, 77)
    created_spendings.append(desc)
    main_page.reload()
    main_page.first_row_description.should_have_text(desc)
    main_page.reload()
    main_page.first_row_description.should_have_text(desc)

@pytest.mark.spending
def test_legend_visible_with_spending(main_page, add_spending, spend_api, spendings_manager):
    spend_api, created_spendings = spendings_manager
    desc = "WithLegend"
    sum = 333
    category = "Entertainment"
    add_spending(desc, sum, category)
    created_spendings.append(desc)
    main_page.reload()
    main_page.legend_container.should_be_visible()
    main_page.legend_list.should_be_visible()
    main_page.legend_item_first.should_have_text(f'{category} {sum} ₽')