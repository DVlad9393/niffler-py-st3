import allure
from playwright.sync_api import Page

from niffler_e_2_e_tests_python.page_factory.button import Button


class Navbar:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.new_spending_button = Button(
            page, locator='a[href="/spending"]', name='Search'
        )
        self.menu_button = Button(
            page, locator='button[aria-label="Menu"]', name='Menu'
        )
        self.profile_button = Button(
            page, locator='a[href="/profile"]', name='Profile'
        )

    def open_new_spending_page(self):
        with allure.step('Opening new spending page'):
            self.new_spending_button.should_be_visible()
            self.new_spending_button.hover()
            self.new_spending_button.click()

    def open_profile_page(self):
        with allure.step('Opening profile page'):
            self.menu_button.should_be_visible()
            self.menu_button.hover()
            self.menu_button.click()
            self.profile_button.should_be_visible()
            self.profile_button.hover()
            self.profile_button.click()