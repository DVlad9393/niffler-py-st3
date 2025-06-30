from dotenv import load_dotenv
import os

load_dotenv()
api_url = os.getenv("API_URL")
from abc import ABC, abstractmethod

import allure
from playwright.sync_api import Locator, Page, expect


class BaseComponent(ABC):
    def __init__(self, page: Page, locator: str, name: str,index: int | None = None) -> None:
        self.page = page
        self.name = name
        self.locator = locator
        self.index = index

    @property
    @abstractmethod
    def type_of(self) -> str:
        return 'component'

    def get_locator(self, **kwargs) -> Locator:
        locator = self.locator.format(**kwargs)
        base_locator = self.page.locator(locator)
        if self.index is not None:
            return base_locator.nth(self.index)
        return base_locator

    def click(
            self,
            intercept_header: bool = False,
            header_key: str = 'authorization',
            url_filter: str = f'{api_url}/api/session/current',
            header_prefix: str = 'Bearer ',
            wait_after_ms: int = 1000,
            **kwargs
    ) -> str | None:
        with allure.step(f'Clicking {self.type_of} with name "{self.name}"'):
            locator = self.get_locator(**kwargs)
            if intercept_header:
                with self.page.expect_request(url_filter) as intercepted:
                    locator.click(timeout=10000)
                    self.page.wait_for_timeout(wait_after_ms)
                req = intercepted.value
                value = req.headers.get(header_key)
                if header_prefix and value and value.startswith(header_prefix):
                    return value.split(header_prefix)[1]
                return value
            else:
                locator.click(timeout=10000)
                return None

    def should_be_visible(self, **kwargs) -> None:
        with allure.step(f'Checking that {self.type_of} "{self.name}" is visible'):
            locator = self.get_locator(**kwargs)
            expect(locator).to_be_visible(timeout=10000)

    def should_not_be_visible(self, **kwargs) -> None:
        with allure.step(f'Checking that {self.type_of} "{self.name}" is not visible'):
            locator = self.get_locator(**kwargs)
            expect(locator).not_to_be_visible(timeout=10000)

    def should_have_text(self, text: str, **kwargs) -> None:
        with allure.step(f'Checking that {self.type_of} "{self.name}" has text "{text}"'):
            locator = self.get_locator(**kwargs)
            expect(locator).to_have_text(text, timeout=10000)

    def should_not_have_text(self, text: str, **kwargs) -> None:
        with allure.step(f'Checking that {self.type_of} "{self.name}" does not have text "{text}"'):
            locator = self.get_locator(**kwargs)
            expect(locator).not_to_have_text(text, timeout=10000)

    def should_be_enabled(self, **kwargs) -> None:
        with allure.step(f'Checking that {self.type_of} "{self.name}" is enabled'):
            locator = self.get_locator(**kwargs)
            expect(locator).to_be_enabled(timeout=10000)