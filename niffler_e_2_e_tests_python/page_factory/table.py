from ..page_factory.base_component import BaseComponent


class Table(BaseComponent):
    @property
    def type_of(self) -> str:
        return 'table'