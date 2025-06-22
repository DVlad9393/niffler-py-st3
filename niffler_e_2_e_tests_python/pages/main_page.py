from playwright.sync_api import Page

from ..page_factory.button import Button
from ..page_factory.title import Title
from ..page_factory.input import Input
from ..page_factory.image import Image
from ..page_factory.text import Text
from ..page_factory.block import Block
from ..page_factory.list_item import ListItem
from ..page_factory.table import Table
from ..page_factory.checkbox import СheckBox
from ..pages.base_page import BasePage

class MainPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

        self.history_of_spending_title = Title(
            page, locator='//h2[contains(text(), "History of Spendings")]', name='Login title')
        self.no_spending_text = Text(page, locator='//p[contains(text(), "There are no spendings")]', name='No spendings text')
        self.niffler_image = Image(page, locator='img[src="/assets/niffler-with-a-coin-Cb77k8MX.png"]', name='Niffler image')

        self.statistics_block = Block(page, locator='//div[@id="stat"]', name='Statistics block')
        self.statistics_title = Title(
            page, locator='#stat h2', name='Statistics title'
        )
        self.statistics_canvas = Block(
            page, locator='#stat canvas', name='Statistics canvas'
        )
        self.legend_container = Block(
            page, locator='#legend-container', name='Legend container'
        )
        self.legend_list = Block(
            page, locator='#legend-container ul', name='Legend list'
        )
        self.legend_item_first = Text(
            page, locator='#legend-container ul li', name='First legend item'
        )

        self.search_input = Input(page, locator='//input[@placeholder="Search"]', name='Search input')
        self.search_button = Button(page, locator='button[type="submit"]', name='Search button')
        self.search_button_icon = Image(page, locator='button[type="submit"] svg', name='Search button icon')
        self.delete_button = Button(page, locator='button[id="delete"]', name='Delete button')
        self.delete_button_dialog = Button(page, locator='div[role="dialog"] button:has-text("Delete")', name='Delete button')
        self.list_of_times = ListItem(page, locator='//div[contains(text(), "All time")]', name='List of times')
        self.list_of_currencies = ListItem(page, locator='//div//span[contains(text(), "ALL")]', name='List of currencies')

        self.spendings_table = Table(
            page, locator='table.MuiTable-root', name='Spendings table'
        )

        self.select_all_checkbox = СheckBox(
            page, locator='thead input[type="checkbox"][aria-label="select all rows"]', name='Select all checkbox'
        )

        self.category_header = Text(
            page, locator='th:has-text("Category")', name='Category header'
        )

        self.amount_header = Text(
            page, locator='th:has-text("Amount")', name='Amount header'
        )

        self.description_header = Text(
            page, locator='th:has-text("Description")', name='Description header'
        )

        self.date_header = Text(
            page, locator='th:has-text("Date")', name='Date header'
        )


        self.first_table_row = ListItem(
            page, locator='tbody tr', name='First spending row'
        )

        self.first_row_checkbox = СheckBox(
            page, locator='tbody tr td input[type="checkbox"]', name='First row checkbox'
        )

        self.first_row_category = Text(
            page, locator='tbody tr td:nth-child(2) span', name='First row category'
        )

        self.first_row_amount = Text(
            page, locator='tbody tr td:nth-child(3) span', name='First row amount'
        )

        self.first_row_description = Text(
            page, locator='tbody tr td:nth-child(4) span', name='First row description'
        )

        self.first_row_date = Text(
            page, locator='tbody tr td:nth-child(5) span', name='First row date'
        )

        self.first_row_edit_button = Button(
            page, locator='tbody tr td button[aria-label="Edit spending"]', name='Edit button in first row'
        )

