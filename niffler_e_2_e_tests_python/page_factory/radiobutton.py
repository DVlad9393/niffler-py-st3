import allure
from playwright.sync_api import expect

from ..page_factory.base_component import BaseComponent


class RadioButton(BaseComponent):
    @property
    def type_of(self) -> str:
        return "radiobutton"

    def hover(self, **kwargs) -> None:
        with allure.step(f'Hovering over {self.type_of} with name "{self.name}"'):
            locator = self.get_locator(**kwargs)
            locator.hover()

    def double_click(self, **kwargs):
        with allure.step(f'Double clicking {self.type_of} with name "{self.name}"'):
            locator = self.get_locator(**kwargs)
            locator.dblclick()

    def should_be_checked(self, **kwargs) -> None:
        with allure.step(f'Checking that {self.type_of} "{self.name}" is checked'):
            locator = self.get_locator(**kwargs)
            expect(locator).to_be_checked(timeout=10000)
