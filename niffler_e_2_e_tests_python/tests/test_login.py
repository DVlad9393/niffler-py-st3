import pytest

from ..pages.login_page import LoginPage
from ..pages.main_page import MainPage

@pytest.mark.login
def test_success_login(login_page: LoginPage, main_page: MainPage, username, password, base_auth_url, base_url):
    login_page.visit(base_auth_url)
    login_page.login(username, password)
    main_page.history_of_spending_title.should_be_visible()
    current_url = main_page.get_current_url()
    assert current_url == base_url

@pytest.mark.login
def test_wrong_password_login(login_page: LoginPage, username, base_auth_url, base_error_url):
    incorrect_password = "incorrect-password"
    login_page.visit(base_auth_url)
    login_page.login(username, incorrect_password)
    login_page.incorrect_login_or_password_text.should_be_visible()
    current_url = login_page.get_current_url()
    assert current_url == base_error_url




