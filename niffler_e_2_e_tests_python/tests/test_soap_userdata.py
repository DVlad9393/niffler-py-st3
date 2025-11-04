import allure
import pytest

from niffler_e_2_e_tests_python.databases.friendship_db import FriendshipDb
from niffler_e_2_e_tests_python.databases.used_db import UsersDb
from niffler_e_2_e_tests_python.utils.userdata_soap_client import UserdataSoapClient


@allure.feature("SOAP / Userdata")
@allure.story("currentUser -> userResponse")
@pytest.mark.soap
def test_current_user_returns_user(userdata_soap: UserdataSoapClient, api_test_user):
    """Проверяет корректность работы SOAP-метода `currentUser`.

    Шаги:
      1. Использует уже зарегистрированного тестового пользователя (`api_test_user`).
      2. Вызывает метод `currentUser` и получает объект пользователя.
      3. Проверяет, что имя и валюта пользователя в ответе совпадают с ожидаемыми значениями.

    Цель:
      Убедиться, что SOAP-метод возвращает актуальные данные пользователя
      и корректно сериализует их в `userResponse.user`.
    """
    username = api_test_user.username

    with allure.step("Вызвать currentUser"):
        user = userdata_soap.current_user(username)

    with allure.step("Проверить содержимое userResponse.user"):
        assert user["username"] == username
        assert user["currency"] in {"RUB", "EUR", "USD", "KZT", None}


@allure.feature("SOAP / Userdata")
@allure.story("friends -> usersResponse")
@pytest.mark.soap
def test_friends_returns_list(userdata_soap: UserdataSoapClient, api_test_user):
    """Проверяет работу метода `friends` в SOAP-сервисе `userdata`.

    Шаги:
      1. Вызывает `friends(username)` для тестового пользователя.
      2. Проверяет, что ответ — это список пользователей-друзей.
      3. Для каждого друга проверяет наличие обязательных полей и допустимых валют.

    Цель:
      Убедиться, что SOAP-ответ корректно сериализует список друзей
      и возвращает валидные поля (username, currency и т.д.).
    """
    username = api_test_user.username

    with allure.step(f"Вызвать friends для {username}"):
        friends = userdata_soap.friends(username)

    with allure.step("Проверить friendsResponse"):
        assert isinstance(friends, list)
        for friend in friends:
            assert "username" in friend
            assert friend["currency"] in {"RUB", "EUR", "USD", "KZT", None}


@allure.feature("SOAP / Userdata")
@allure.story("updateUser -> userResponse")
@pytest.mark.soap
def test_update_user_changes_currency(userdata_soap: UserdataSoapClient, api_test_user):
    """Проверяет, что метод `updateUser` корректно изменяет данные пользователя.

    Шаги:
      1. Отправляет SOAP-запрос `updateUser` с новой валютой ("USD").
      2. Проверяет, что в ответе вернулась обновлённая информация.
      3. Делает повторный вызов `currentUser` для валидации изменения в системе.

    Цель:
      Убедиться, что обновление пользователя через SOAP отражается в хранилище данных,
      а возвращаемое значение корректно отражает новое состояние пользователя.
    """
    username = api_test_user.username
    new_data = {"username": username, "currency": "USD"}

    with allure.step("Обновить пользователя через SOAP"):
        updated = userdata_soap.update_user(new_data)

    assert updated["username"] == username
    assert updated["currency"] == "USD"

    with allure.step("Вызвать currentUser"):
        user = userdata_soap.current_user(username)

    with allure.step("Проверить обновленное содержимое user"):
        assert user["username"] == username
        assert user["currency"] == "USD"


@allure.feature("SOAP / Userdata")
@allure.story("sendInvitation / acceptInvitation")
@pytest.mark.soap
def test_accept_friendship(
    userdata_soap: UserdataSoapClient,
    two_api_users,
    db_client: UsersDb,
    friendship_db: FriendshipDb,
):
    """Проверяет полное создание и принятие дружбы через SOAP-сервис.

    Шаги:
      1. Создаёт двух пользователей A и B.
      2. Удаляет возможные старые связи в таблице `friendship`.
      3. Отправляет приглашение (A → B) через `sendInvitation`.
      4. Проверяет в БД, что запись о дружбе появилась со статусом `PENDING`.
      5. Принимает приглашение (B → A) через `acceptInvitation`.
      6. Проверяет, что статус дружбы изменился на `ACCEPTED`.

    Цель:
      Убедиться, что SOAP-вызовы корректно синхронизируются с таблицей `friendship`,
      и статусы дружбы последовательно переходят от PENDING → ACCEPTED.
    """
    user_a, user_b = two_api_users  # A отправляет, B принимает

    a = db_client.wait_for_user_appears(user_a.username, timeout=25.0).id
    b = db_client.wait_for_user_appears(user_b.username, timeout=25.0).id

    friendship_db.delete_between(a, b)

    with allure.step("Отправить приглашение (A -> B)"):
        sent = userdata_soap.send_invitation(user_a.username, user_b.username)
        assert sent["friendshipStatus"] in ("INVITE_SENT", "VOID", "FRIEND", None)
        row = friendship_db.wait_for_link(a, b, status="PENDING", timeout=20.0)
        assert row.requester_id == a and row.addressee_id == b

    with allure.step("Принять приглашение (B принимает A)"):
        accepted = userdata_soap.accept_invitation(user_b.username, user_a.username)
        assert accepted["friendshipStatus"] in ("FRIEND", "VOID", None)
        row = friendship_db.wait_for_link(a, b, status="ACCEPTED", timeout=20.0)
        assert row.requester_id == a and row.addressee_id == b


@allure.feature("SOAP / Userdata")
@allure.story("sendInvitation / declineInvitation")
@pytest.mark.soap
def test_decline_friendship(
    userdata_soap: UserdataSoapClient,
    two_api_users,
    db_client: UsersDb,
    friendship_db: FriendshipDb,
):
    """Проверяет сценарий отклонения дружбы через SOAP-интерфейс.

    Шаги:
      1. Создаёт двух тестовых пользователей A и B.
      2. Удаляет возможные старые связи между ними.
      3. A отправляет приглашение B через `sendInvitation`.
      4. Проверяет, что в таблице появилась запись со статусом `PENDING`.
      5. B отклоняет приглашение через `declineInvitation`.
      6. Проверяет, что SOAP-ответ возвращает `VOID` и запись friendship удалена из БД.

    Цель:
      Убедиться, что отклонение дружбы корректно отражается в SOAP-ответе
      и приводит к удалению соответствующей записи из таблицы `friendship`.
    """
    user_a, user_b = two_api_users  # A отправляет, B принимает

    a = db_client.wait_for_user_appears(user_a.username, timeout=25.0).id
    b = db_client.wait_for_user_appears(user_b.username, timeout=25.0).id

    friendship_db.delete_between(a, b)

    with allure.step("Отправить приглашение (A -> B)"):
        sent = userdata_soap.send_invitation(user_a.username, user_b.username)
        assert sent["friendshipStatus"] in ("INVITE_SENT", "VOID", "FRIEND", None)
        row = friendship_db.wait_for_link(a, b, status="PENDING", timeout=20.0)
        assert row.requester_id == a and row.addressee_id == b

    with allure.step("Отклонить/сбросить дружбу (B отклоняет A)"):
        declined = userdata_soap.decline_invitation(user_b.username, user_a.username)
        assert declined["friendshipStatus"] in ("VOID", None)
        assert friendship_db.get_between(a, b) == []
