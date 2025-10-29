import allure
import pytest

from ..pages.login_page import LoginPage
from ..pages.main_page import MainPage


@allure.feature("Authentication")
@allure.story("Successful Login")
@pytest.mark.login
def test_success_login(login_page: LoginPage, main_page: MainPage, envs, api_test_user):
    login_page.visit(envs.base_auth_url)
    login_page.login(api_test_user.username, api_test_user.password)
    main_page.history_of_spending_title.should_be_visible()
    current_url = main_page.get_current_url()
    assert current_url == envs.base_url


@allure.feature("Authentication")
@allure.story("Wrong Password Login")
@pytest.mark.login
def test_wrong_password_login(login_page: LoginPage, envs, api_test_user):
    incorrect_password = "incorrect-password"
    assert api_test_user.password != incorrect_password
    login_page.visit(envs.base_auth_url)
    login_page.login(api_test_user.username, incorrect_password)
    login_page.incorrect_login_or_password_text.should_be_visible()
    current_url = login_page.get_current_url()
    assert current_url == envs.base_error_url
