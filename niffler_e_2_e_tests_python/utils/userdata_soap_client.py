from __future__ import annotations

import xml.etree.ElementTree as ET  # noqa: N817
from typing import Any

import allure

from niffler_e_2_e_tests_python.utils.soap_client import SoapClient


def _text(el: ET.Element | None) -> str | None:
    """Безопасно возвращает текстовое содержимое XML-элемента или `None`, если оно отсутствует."""
    return el.text.strip() if el is not None and el.text else None


class UserdataSoapClient:
    """SOAP-клиент для взаимодействия с сервисом **niffler-userdata** по контракту `userdata.wsdl`.

    Класс инкапсулирует работу с методами SOAP-интерфейса, включая:
      • получение информации о пользователях (`currentUser`, `allUsers`);
      • обновление данных (`updateUser`);
      • управление дружбой (`sendInvitation`, `acceptInvitation`, `declineInvitation`, `removeFriend`);
      • получение списка друзей (`friends`).

    Все запросы и ответы автоматически логируются в **Allure** как XML-вложения для удобства отладки.
    """

    def __init__(self, endpoint: str, ns: str):
        """Инициализирует SOAP-клиент для `userdata.wsdl`.

        :param endpoint: URL SOAP-эндпойнта (например, `http://localhost:8080/ws`).
        :param ns: Пространство имён бизнес-схемы (например, `"niffler-userdata"`).
        """
        self.soap = SoapClient(endpoint, ns)

    def current_user(self, username: str) -> dict[str, Any]:
        """Получает полную информацию о пользователе по его `username`.

        Отправляет SOAP-запрос `<currentUserRequest>` и парсит `<userResponse>`,
        возвращая атрибуты пользователя в виде словаря.

        :param username: Имя пользователя (логин) в системе.
        :return: Словарь с данными пользователя (`id`, `username`, `firstname`, `surname`, `currency`, и т.д.).
        :raises AssertionError: Если в ответе отсутствует тег `<user>`.
        """
        inner = f"""
        <ud:currentUserRequest xmlns:ud="{self.soap.ns}">
          <ud:username>{username}</ud:username>
        </ud:currentUserRequest>
        """.strip()

        with allure.step(f"SOAP currentUser({username})"):
            root = self.soap.call(inner)

        user_node = root.find(".//{*}user")
        if user_node is None:
            raise AssertionError("В ответе отсутствует <user>")
        return self._user_from_node(user_node)

    def update_user(self, user: dict[str, Any]) -> dict[str, Any]:
        """Обновляет данные пользователя через SOAP-метод `updateUser`.

        При отсутствии `id` автоматически вызывает `current_user` для его получения.

        :param user: Словарь с полями пользователя (минимум `username`, опционально `currency`, `id`).
        :return: Обновлённая информация о пользователе из `<userResponse>`.
        :raises AssertionError: Если в ответе отсутствует `<user>` или не удалось определить `id`.
        """
        username = user["username"]

        if not user.get("id"):
            cur = self.current_user(username)
            if not cur.get("id"):
                raise AssertionError(f"currentUser('{username}') вернул пустой id")
            user["id"] = cur["id"]

        with allure.step(f"SOAP updateUser({username})"):
            user_xml = f"""
            <ud:updateUserRequest xmlns:ud="{self.soap.ns}">
              <ud:user>
                <ud:id>{user['id']}</ud:id>
                <ud:username>{username}</ud:username>
                <ud:currency>{user.get('currency', 'RUB')}</ud:currency>
              </ud:user>
            </ud:updateUserRequest>
            """.strip()
            root = self.soap.call(user_xml)

        node = root.find(".//{*}user")
        if node is None:
            raise AssertionError("В ответе отсутствует <user>")
        return self._user_from_node(node)

    def all_users(
        self, username: str, search_query: str | None = None
    ) -> dict[str, Any]:
        """Возвращает список всех пользователей (с пагинацией и метаданными).

        :param username: Имя пользователя, от имени которого совершается запрос.
        :param search_query: Опциональный поисковый фильтр.
        :return: Словарь:
            {
              "users": [ {…}, … ],
              "meta": { "size": int, "number": int, "totalElements": int, "totalPages": int }
            }
        """
        parts = [
            f'<ud:allUsersRequest xmlns:ud="{self.soap.ns}">',
            f"<ud:username>{username}</ud:username>",
        ]
        if search_query:
            parts.append(f"<ud:searchQuery>{search_query}</ud:searchQuery>")
        parts.append("</ud:allUsersRequest>")
        inner = "".join(parts)

        with allure.step(f"SOAP allUsers({username})"):
            root = self.soap.call(inner)

        users = [self._user_from_node(u) for u in root.findall(".//{*}user")]
        meta = {
            "size": int(_text(root.find(".//{*}size")) or 0),
            "number": int(_text(root.find(".//{*}number")) or 0),
            "totalElements": int(_text(root.find(".//{*}totalElements")) or 0),
            "totalPages": int(_text(root.find(".//{*}totalPages")) or 0),
        }
        return {"users": users, "meta": meta}

    def friends(
        self, username: str, search_query: str | None = None
    ) -> list[dict[str, Any]]:
        """Возвращает список друзей указанного пользователя.

        :param username: Имя пользователя (логин).
        :param search_query: Опциональный фильтр поиска по имени друга.
        :return: Список словарей с данными друзей.
        """
        parts = [
            f'<ud:friendsRequest xmlns:ud="{self.soap.ns}">',
            f"<ud:username>{username}</ud:username>",
        ]
        if search_query:
            parts.append(f"<ud:searchQuery>{search_query}</ud:searchQuery>")
        parts.append("</ud:friendsRequest>")
        inner = "".join(parts)

        with allure.step(f"SOAP friends({username})"):
            root = self.soap.call(inner)

        return [self._user_from_node(u) for u in root.findall(".//{*}user")]

    def send_invitation(self, username: str, target: str) -> dict[str, Any]:
        """Отправляет приглашение в друзья (SOAP `sendInvitationRequest`).

        :param username: Имя пользователя, отправляющего приглашение.
        :param target: Имя пользователя, которому отправляется приглашение.
        :return: Словарь `<user>` из ответа, включая `friendshipStatus`.
        :raises AssertionError: Если у отправителя отсутствует `id`.
        """
        cur = self.current_user(username)
        if not cur.get("id"):
            raise AssertionError(f"currentUser('{username}') вернул пустой id")

        inner = f"""
        <ud:sendInvitationRequest xmlns:ud="{self.soap.ns}">
          <ud:username>{username}</ud:username>
          <ud:friendToBeRequested>{target}</ud:friendToBeRequested>
        </ud:sendInvitationRequest>
        """.strip()
        with allure.step(f"SOAP sendInvitation({username} → {target})"):
            root = self.soap.call(inner)
        return self._user_from_node(root.find(".//{*}user"))

    def accept_invitation(self, username: str, target: str) -> dict[str, Any]:
        """Принимает входящее приглашение в друзья (SOAP `acceptInvitationRequest`).

        :param username: Имя пользователя, который принимает приглашение.
        :param target: Имя пользователя, отправившего приглашение.
        :return: Словарь `<user>` с актуальным статусом дружбы.
        :raises AssertionError: Если у пользователя отсутствует `id`.
        """
        cur = self.current_user(username)
        if not cur.get("id"):
            raise AssertionError(f"currentUser('{username}') вернул пустой id")
        target_user = self.current_user(target)
        if not target_user.get("id"):
            allure.attach(
                str(target), "target_not_found.txt", allure.attachment_type.TEXT
            )

        inner = f"""
        <ud:acceptInvitationRequest xmlns:ud="{self.soap.ns}">
          <ud:username>{username}</ud:username>
          <ud:friendToBeAdded>{target}</ud:friendToBeAdded>
        </ud:acceptInvitationRequest>
        """.strip()
        with allure.step(f"SOAP acceptInvitation({username} ← {target})"):
            root = self.soap.call(inner)
        return self._user_from_node(root.find(".//{*}user"))

    def decline_invitation(self, username: str, target: str) -> dict[str, Any]:
        """Отклоняет приглашение в друзья (SOAP `declineInvitationRequest`).

        :param username: Имя пользователя, отклоняющего приглашение.
        :param target: Имя пользователя, чьё приглашение отклоняется.
        :return: Словарь `<user>` из ответа, включающий `friendshipStatus`.
        :raises AssertionError: Если `currentUser` вернул пустой `id`.
        """
        cur = self.current_user(username)
        if not cur.get("id"):
            raise AssertionError(f"currentUser('{username}') вернул пустой id")

        inner = f"""
        <ud:declineInvitationRequest xmlns:ud="{self.soap.ns}">
          <ud:username>{username}</ud:username>
          <ud:invitationToBeDeclined>{target}</ud:invitationToBeDeclined>
        </ud:declineInvitationRequest>
        """.strip()
        with allure.step(f"SOAP declineInvitation({username} X {target})"):
            root = self.soap.call(inner)
        return self._user_from_node(root.find(".//{*}user"))

    def remove_friend(self, username: str, target: str) -> None:
        """Удаляет существующего друга (SOAP `removeFriendRequest`).

        :param username: Пользователь, инициирующий удаление.
        :param target: Пользователь, которого нужно удалить из друзей.
        :raises AssertionError: Если `currentUser` не вернул `id`.
        """
        cur = self.current_user(username)
        if not cur.get("id"):
            raise AssertionError(f"currentUser('{username}') вернул пустой id")

        inner = f"""
        <ud:removeFriendRequest xmlns:ud="{self.soap.ns}">
          <ud:username>{username}</ud:username>
          <ud:friendToBeRemoved>{target}</ud:friendToBeRemoved>
        </ud:removeFriendRequest>
        """.strip()
        with allure.step(f"SOAP removeFriend({username} - {target})"):
            self.soap.call(inner)

    @staticmethod
    def _user_from_node(node: ET.Element) -> dict[str, Any]:
        """Преобразует XML-элемент `<user>` из SOAP-ответа в Python-словарь.

        Включает основные поля, возвращаемые сервисом `userdata`.

        :param node: XML-элемент `<user>`.
        :return: Словарь с ключами:
            `id`, `username`, `firstname`, `surname`, `fullname`,
            `currency`, `photo`, `photoSmall`, `friendshipStatus`.
        """
        return {
            "id": _text(node.find(".//{*}id")),
            "username": _text(node.find(".//{*}username")),
            "firstname": _text(node.find(".//{*}firstname")),
            "surname": _text(node.find(".//{*}surname")),
            "fullname": _text(node.find(".//{*}fullname")),
            "currency": _text(node.find(".//{*}currency")),
            "photo": _text(node.find(".//{*}photo")),
            "photoSmall": _text(node.find(".//{*}photoSmall")),
            "friendshipStatus": _text(node.find(".//{*}friendshipStatus")),
        }
