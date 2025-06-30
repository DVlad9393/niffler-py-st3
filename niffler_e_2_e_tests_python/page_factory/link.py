from ..page_factory.base_component import BaseComponent


class Link(BaseComponent):
    @property
    def type_of(self) -> str:
        return 'link'