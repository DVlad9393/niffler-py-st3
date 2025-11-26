from niffler_e_2_e_tests_python.page_factory.base_component import BaseComponent


class Title(BaseComponent):
    @property
    def type_of(self) -> str:
        return "title"
