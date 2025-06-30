import pytest

from ..pages.login_page import LoginPage

@pytest.mark.register
def test_registration_flow(login_page: LoginPage, create_test_data, base_auth_url):
    username, password = create_test_data
    login_page.create_new_account(username, password)
    current_url = login_page.get_current_url()
    assert current_url == base_auth_url