from ..page_factory.base_component import BaseComponent


class Block(BaseComponent):
    @property
    def type_of(self) -> str:
        return 'block'