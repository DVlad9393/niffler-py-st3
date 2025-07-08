from ..page_factory.base_component import BaseComponent


class Image(BaseComponent):
    @property
    def type_of(self) -> str:
        return "image"
