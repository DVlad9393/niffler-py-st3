import allure
from playwright.sync_api import Page, expect

from niffler_e_2_e_tests_python.page_factory.button import Button
from niffler_e_2_e_tests_python.page_factory.title import Title
from niffler_e_2_e_tests_python.page_factory.input import Input
from niffler_e_2_e_tests_python.pages.base_page import BasePage
from niffler_e_2_e_tests_python.page_factory.checkbox import СheckBox

class ProfilePage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

        self.title = Title(
            page, locator='//h2[contains(text(), "Profile")]', name='Profile')

        self.load_picture_button = Button(
            page, locator='label[for="image__input"]', name='Load picture'
        )

        self.username_input = Input(
            page, locator='input[name="username"]', name='Username'
        )

        self.name_input = Input(
            page, locator='input[name="name"]', name='Name'
        )

        self.save_button = Button(
            page, locator='button[type="submit"]', name='Save'
        )

        self.show_archive_checkbox = СheckBox(
            page, locator='input[type="checkbox"]', name='Show archive'
        )

        self.title = Title(
            page, locator='//h2[contains(text(), "Categories")]', name='Categories')

        self.add_category_input = Input(
            page, locator='input[placeholder="Add new category"]', name='Category'
        )

        self._categories_chips = self.page.locator('div[class*="MuiBox-root css-1lekzkb"]')

        self.category_placeholder = Input(self.page,'input[placeholder="Edit category"]', name='Category placeholder')

        self.close_edit_category_button = Button(
            page, locator='button[aria-label="close"]', name='Close edit category'
        )

        self.archive_category_submit_button = Button(
            page, locator='xpath=//button[text() = "Archive"]', name='Archive category'
        )

        self.unarchive_category_submit_button = Button(
            page, locator='xpath=//button[text() = "Unarchive"]', name='Unarchive category')

    def add_category(self, category: str) -> None:
        with allure.step(f'Adding category "{category}"'):
            self.add_category_input.fill(category)
            self.page.keyboard.press('Enter')
            food_button = Button(self.page, f'//div/span[text() = "{category}"]', 'Категория')
            food_button.should_be_enabled()
            food_button.should_be_visible()


    def edit_category_name(self, old_category_name: str, new_category_name: str) -> None:
        with allure.step(f'Editing category "{old_category_name}" -> "{new_category_name}"'):
            chips_button_old_category = Button (self.page, f'//div/span[text() = "{old_category_name}"]', 'Старая категория')
            chips_button_old_category.should_be_enabled()
            chips_button_old_category.hover()
            chips_button_old_category.click()

            self.category_placeholder.click()
            self.category_placeholder.clear()
            self.category_placeholder.input_text(new_category_name)
            self.page.keyboard.press('Enter')
            chips_button_new_category = Button (self.page, f'//div/span[text() = "{new_category_name}"]', 'Новая категория')
            chips_button_new_category.should_be_visible(timeout=5000)
            chips_button_old_category.should_not_be_visible(timeout=5000)

    def archive_category(self, category: str) -> None:
        with allure.step(f'Archiving category "{category}"'):

            archive_category = Button(self.page,
                                      f'xpath=//div/span[text() = "{category}"]/ancestor::div[@class][2]//button[contains(@class, "MuiIconButton-root") and @aria-label="Archive category"]',
                                      'Архивировать категорию')
            archive_category.should_be_enabled()
            archive_category.hover()
            archive_category.click()

            self.archive_category_submit_button.should_be_enabled(timeout=3000)
            self.archive_category_submit_button.click()
            chips_button_category = Button(self.page, f'xpath=//div/span[text() = "{category}"]',
                                               'Категория')
            chips_button_category.should_not_be_visible(timeout=5000)
            self.show_archive_checkbox.click()
            chips_button_category.should_be_visible(timeout=5000)
            self.show_archive_checkbox.click()

    def unarchive_category(self, category: str) -> None:
        with allure.step(f'Unarchiving category "{category}"'):
            self.show_archive_checkbox.click()
            unarchive_category = Button(self.page,
                                      f'xpath=//div/span[text() = "{category}"]/ancestor::div[@class][2]//button[contains(@class, "MuiIconButton-root") and @aria-label="Unarchive category"]',
                                      'Разархивировать категорию')
            unarchive_category.should_be_enabled()
            unarchive_category.hover()
            unarchive_category.click()
            self.unarchive_category_submit_button.click()


            chips_button_category = Button(self.page, f'xpath=//div/span[text() = "{category}"]',
                                               'Категория')
            self.show_archive_checkbox.click()
            chips_button_category.should_be_visible(timeout=5000)
            chips_button_category.should_be_enabled()