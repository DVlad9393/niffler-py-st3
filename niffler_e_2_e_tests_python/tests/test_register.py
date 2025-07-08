import allure
import pytest

from ..pages.login_page import LoginPage


@allure.feature("Authentication")
@allure.story("Registration Flow")
@pytest.mark.register
def test_registration_flow(login_page: LoginPage, create_test_data, envs):
    username, password = create_test_data
    login_page.create_new_account(username, password)
    current_url = login_page.get_current_url()
    assert current_url == envs.base_auth_url
