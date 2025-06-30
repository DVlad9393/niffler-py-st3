from ..page_factory.base_component import BaseComponent


class ListItem(BaseComponent):
    @property
    def type_of(self) -> str:
        return 'list item'