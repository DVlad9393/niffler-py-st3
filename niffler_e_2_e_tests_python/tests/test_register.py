from ..pages.login_page import LoginPage
from dotenv import load_dotenv
import os

load_dotenv()
base_auth_url = os.getenv("BASE_AUTH_URL")

def test_registration_flow(login_page: LoginPage, create_test_data):
    username, password = create_test_data
    login_page.create_new_account(username, password)
    current_url = login_page.get_current_url()
    assert current_url == base_auth_url