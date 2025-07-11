import allure

from ..page_factory.base_component import BaseComponent


class Button(BaseComponent):
    @property
    def type_of(self) -> str:
        return "button"

    def hover(self, **kwargs) -> None:
        with allure.step(f'Hovering over {self.type_of} with name "{self.name}"'):
            locator = self.get_locator(**kwargs)
            locator.hover()

    def double_click(self, **kwargs):
        with allure.step(f'Double clicking {self.type_of} with name "{self.name}"'):
            locator = self.get_locator(**kwargs)
            locator.dblclick()
