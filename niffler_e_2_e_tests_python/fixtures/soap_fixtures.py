import pytest

from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.utils.userdata_soap_client import UserdataSoapClient


@pytest.fixture(scope="session")
def userdata_soap(envs: Envs) -> UserdataSoapClient:
    """Создаёт клиент SOAP для взаимодействия с сервисом `userdata`.

    Фикстура инициализируется один раз за сессию pytest (`scope="session"`)
    и возвращает экземпляр `UserdataSoapClient`, настроенный на актуальный endpoint
    и namespace из переменных окружения (`envs`).

    Этот клиент используется в SOAP-тестах (например, `test_current_user_returns_user`
    или `test_friendship_flow`) для отправки запросов вида
    `currentUser`, `updateUser`, `sendInvitation` и т.д.

    Все запросы внутри клиента автоматически логируются в Allure-отчёт
    как вложения с XML-запросами и ответами.

    :param envs: Объект конфигурации окружения (`Envs`), содержащий SOAP endpoint
                 (`userdata_soap_url`) и пространство имён (`userdata_soap_ns`).
    :return: Инициализированный клиент `UserdataSoapClient` для тестов SOAP API.
    """
    return UserdataSoapClient(endpoint=envs.userdata_soap_url, ns=envs.userdata_soap_ns)
