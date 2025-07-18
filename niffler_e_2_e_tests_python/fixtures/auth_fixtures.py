import pytest

from niffler_e_2_e_tests_python.utils.auth_client import AuthClient


@pytest.fixture(scope="session")
def api_auth_token(envs) -> str:
    """Фикстура для получения access_token для API-тестов (через AuthClient, минуя браузер)."""
    client = AuthClient(envs)
    return client.get_token(envs.username, envs.password)
