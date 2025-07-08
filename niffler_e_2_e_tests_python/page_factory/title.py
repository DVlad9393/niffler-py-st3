from ..page_factory.base_component import BaseComponent


class Title(BaseComponent):
    @property
    def type_of(self) -> str:
        return "title"
