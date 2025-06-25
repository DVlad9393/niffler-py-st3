from playwright.sync_api import Page

from niffler_e_2_e_tests_python.page_factory.button import Button
from niffler_e_2_e_tests_python.page_factory.text import Text
from niffler_e_2_e_tests_python.page_factory.title import Title
from niffler_e_2_e_tests_python.page_factory.input import Input
from niffler_e_2_e_tests_python.page_factory.list_item import ListItem
from niffler_e_2_e_tests_python.pages.base_page import BasePage

class NewSpendingPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

        self.title = Title(
            page, locator='//h2[contains(text(), "Add new spending")]', name='Add new spending title'
        )

        self.amount_input = Input(
            page, locator='#amount', name='Amount input'
        )

        self.currency_select = ListItem(
            page, locator='#currency', name='Currency select'
        )

        self.currency_option_rub = ListItem(
            page, locator='ul[role="listbox"] li:has-text("RUB")', name='Currency RUB option'
        )

        self.category_input = Input(
            page, locator='#category', name='Category input'
        )

        self.date_input = Input(
            page, locator='input[name="date"]', name='Date input'
        )
        self.date_picker_button = Button(
            page, locator='button[aria-label^="Choose date"]', name='Date picker button'
        )

        self.description_input = Input(
            page, locator='#description', name='Description input'
        )

        self.cancel_button = Button(
            page, locator='#cancel', name='Cancel button'
        )

        self.add_button = Button(
            page, locator='#save', name='Add button'
        )

        self.error_amount_message = Text(
            page, locator='//span[contains(text(), "Amount has to be")]', name='Error message'
        )

        self.error_no_category_message = Text(
            page, locator='//span[contains(text(), "Please choose category")]', name='Error message'
        )