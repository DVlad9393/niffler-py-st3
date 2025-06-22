from playwright.sync_api import Page

from niffler_e_2_e_tests_python.page_factory.button import Button


class Navbar:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.new_spending_button = Button(
            page, locator='a[href="/spending"]', name='Search'
        )

    def open_new_spending_page(self):
        self.new_spending_button.should_be_visible()
        self.new_spending_button.hover()
        self.new_spending_button.click()