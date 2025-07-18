from collections.abc import Generator
from typing import Any

import allure
import pytest
from playwright.sync_api import Page, sync_playwright

from niffler_e_2_e_tests_python.pages.login_page import LoginPage
from niffler_e_2_e_tests_python.pages.main_page import MainPage
from niffler_e_2_e_tests_python.pages.new_spending_page import NewSpendingPage
from niffler_e_2_e_tests_python.pages.profile_page import ProfilePage


@pytest.fixture(scope="function", params=["chromium"])
def browser_page(request) -> Generator[Any, Any]:
    """Фикстура для создания страницы браузера Playwright.

    :param request: Параметризировано браузером ('chromium', по умолчанию).
    :yields: Экземпляр страницы Playwright Page.
    Делает скриншот и прикладывает видео после завершения теста.
    """
    browser_name = request.param
    with sync_playwright() as playwright:
        browser = getattr(playwright, browser_name).launch(
            headless=False, args=["--start-maximized", "--window-position=0,0"]
        )
        context = browser.new_context(
            viewport={"width": 1600, "height": 900}, record_video_dir="allure-results/"
        )
        page = context.new_page()

        yield page

        allure.attach(
            page.screenshot(),
            name="screenshot",
            attachment_type=allure.attachment_type.PNG,
        )

        video = page.video.path()
        page.close()
        context.close()
        allure.attach.file(
            video,
            name="video",
            attachment_type=allure.attachment_type.WEBM,
        )


@pytest.fixture(scope="function")
def main_page(browser_page: Page) -> MainPage:
    """Фикстура возвращает объект главной страницы (MainPage) для работы с UI.

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр MainPage.
    """
    return MainPage(browser_page)


@pytest.fixture(scope="function")
def login_page(browser_page: Page) -> LoginPage:
    """Фикстура возвращает объект страницы логина (LoginPage).

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр LoginPage.
    """
    return LoginPage(browser_page)


@pytest.fixture(scope="function")
def new_spending_page(browser_page: Page) -> NewSpendingPage:
    """Фикстура возвращает объект страницы создания новой траты (NewSpendingPage).

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр NewSpendingPage.
    """
    return NewSpendingPage(browser_page)


@pytest.fixture(scope="function")
def profile_page(browser_page: Page) -> ProfilePage:
    """Фикстура возвращает объект страницы профиля (ProfilePage).

    :param browser_page: Экземпляр страницы браузера.
    :return: Экземпляр ProfilePage.
    """
    return ProfilePage(browser_page)
