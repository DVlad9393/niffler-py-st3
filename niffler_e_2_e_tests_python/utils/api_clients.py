from datetime import datetime
from functools import wraps
from typing import Any

import allure
import httpx

from niffler_e_2_e_tests_python.models.category import CategoryDTO
from niffler_e_2_e_tests_python.models.spend import SpendAdd, SpendDTO
from niffler_e_2_e_tests_python.utils.base_session import BaseSession


def check_status_allure(func):
    """Декоратор для проверки статуса ответа с логированием через allure."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        resp = func(*args, **kwargs)
        with allure.step(f"Check status ({resp.status_code})"):
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                allure.attach(
                    resp.text,
                    name=f"HTTP error {resp.status_code} response body",
                    attachment_type=allure.attachment_type.TEXT,
                )
                if e.response.status_code not in (200, 201):
                    e.add_note(resp.text)
                    raise e
        return resp

    return wrapper


class BaseApiClient:
    def __init__(self, session: BaseSession, token: str) -> None:
        """Инициализирует API клиент с сессией и токеном авторизации.

        :param session: Экземпляр сессии для выполнения HTTP-запросов.
        :param token: JWT-токен для авторизации.
        """
        self.session = session
        self.set_token(token)

    def set_token(self, token: str) -> None:
        """Устанавливает токен авторизации для последующих запросов.

        :param token: JWT-токен для авторизации.
        """
        with allure.step("Set token"):
            self.token = token
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @check_status_allure
    def _get(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP GET-запрос через текущую сессию и возвращает ответ.

        :param args: Позиционные аргументы, передаваемые в self.session.get
        :param kwargs: Именованные аргументы, передаваемые в self.session.get
        :return: Объект httpx.Response с данными ответа
        """
        return self.session.get(*args, **kwargs)

    @check_status_allure
    def _post(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP POST-запрос через текущую сессию и возвращает ответ.

        :param args: Позиционные аргументы, передаваемые в self.session.post
        :param kwargs: Именованные аргументы, передаваемые в self.session.post
        :return: Объект httpx.Response с данными ответа
        """
        return self.session.post(*args, **kwargs)

    @check_status_allure
    def _patch(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP PATCH-запрос через текущую сессию и возвращает ответ.

        :param args: Позиционные аргументы, передаваемые в self.session.patch
        :param kwargs: Именованные аргументы, передаваемые в self.session.patch
        :return: Объект httpx.Response с данными ответа
        """
        return self.session.patch(*args, **kwargs)

    @check_status_allure
    def _delete(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP DELETE-запрос через текущую сессию и возвращает ответ.

        :param args: Позиционные аргументы, передаваемые в self.session.delete
        :param kwargs: Именованные аргументы, передаваемые в self.session.delete
        :return: Объект httpx.Response с данными ответа
        """
        return self.session.delete(*args, **kwargs)

    def _get_raw(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP GET-запрос через текущую сессию и возвращает ответ
        **без автоматической проверки статуса**.

        :param args: Позиционные аргументы, передаваемые в self.session.get
        :param kwargs: Именованные аргументы, передаваемые в self.session.get
        :return: Объект httpx.Response с данными ответа (ошибки не выбрасываются)
        """
        return self.session.get(*args, **kwargs)

    def _post_raw(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP POST-запрос через текущую сессию и возвращает ответ
        **без автоматической проверки статуса**.

        :param args: Позиционные аргументы, передаваемые в self.session.post
        :param kwargs: Именованные аргументы, передаваемые в self.session.post
        :return: Объект httpx.Response с данными ответа (ошибки не выбрасываются)
        """
        return self.session.post(*args, **kwargs)

    def _patch_raw(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP PATCH-запрос через текущую сессию и возвращает ответ
        **без автоматической проверки статуса**.

        :param args: Позиционные аргументы, передаваемые в self.session.patch
        :param kwargs: Именованные аргументы, передаваемые в self.session.patch
        :return: Объект httpx.Response с данными ответа (ошибки не выбрасываются)
        """
        return self.session.patch(*args, **kwargs)

    def _delete_raw(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Выполняет HTTP DELETE-запрос через текущую сессию и возвращает ответ
        **без автоматической проверки статуса**.

        :param args: Позиционные аргументы, передаваемые в self.session.delete
        :param kwargs: Именованные аргументы, передаваемые в self.session.delete
        :return: Объект httpx.Response с данными ответа (ошибки не выбрасываются)
        """
        return self.session.delete(*args, **kwargs)


class CategoriesApiClient(BaseApiClient):
    def get_all_categories(self, exclude_archived: bool = False) -> list[CategoryDTO]:
        """Получает список всех категорий пользователя."""
        with allure.step("Get all categories"):
            resp = self._get(
                "/api/categories/all",
                params={"excludeArchived": exclude_archived},
                headers=self.headers,
            )
            return [CategoryDTO.model_validate(item) for item in resp.json()]

    def add_category(self, category_name: str) -> CategoryDTO:
        """Создаёт новую категорию."""
        with allure.step("Add category"):
            payload = {"name": category_name}
            resp = self._post("/api/categories/add", json=payload, headers=self.headers)
            return CategoryDTO.model_validate(resp.json())

    def add_duplicate_category(self, category_name: str) -> httpx.Response:
        """Создаёт новую дублирующую категорию."""
        with allure.step("Add duplicate category"):
            payload = {"name": category_name}
            resp = self._post_raw(
                "/api/categories/add", json=payload, headers=self.headers
            )
            return resp

    def update_category(
        self, category_id: str, category_name: str, archived: bool
    ) -> CategoryDTO:
        """Обновляет существующую категорию."""
        with allure.step("Update category"):
            payload = {"id": category_id, "name": category_name, "archived": archived}
            resp = self._patch(
                "/api/categories/update", json=payload, headers=self.headers
            )
            return CategoryDTO.model_validate(resp.json())


class SpendApiClient(BaseApiClient):
    def get_all_spends(
        self, filter_currency: str = None, filter_period: str = None
    ) -> list[SpendDTO]:
        """Получает список всех трат пользователя с возможностью фильтрации."""
        with allure.step("Get all spends"):
            params = {}
            if filter_currency:
                params["filterCurrency"] = filter_currency
            if filter_period:
                params["filterPeriod"] = filter_period
            resp = self._get("/api/spends/all", params=params, headers=self.headers)
            return [SpendDTO.model_validate(item) for item in resp.json()]

    def get_spending_by_id(self, spend_id: str) -> SpendDTO:
        """Получает трату по ее идентификатору."""
        with allure.step("Get spending by id"):
            resp = self._get(f"/api/spends/{spend_id}", headers=self.headers)
            return SpendDTO.model_validate(resp.json())

    def get_not_exists_spending_by_id(self, spend_id: str) -> httpx.Response:
        """Получает несуществующую трату по ее идентификатору."""
        with allure.step("Get not exists spending by id"):
            resp = self._get_raw(f"/api/spends/{spend_id}", headers=self.headers)
            return resp

    def add_spending(
        self, spend: SpendAdd, category: CategoryDTO, username: str
    ) -> SpendDTO:
        """Добавляет новую трату."""
        with allure.step("Add spending"):
            payload = spend.model_dump()
            if isinstance(payload.get("spendDate"), datetime):
                payload["spendDate"] = payload["spendDate"].isoformat()
            payload["category"] = category.model_dump()
            payload["username"] = username
            resp = self._post("/api/spends/add", json=payload, headers=self.headers)
            return SpendDTO.model_validate(resp.json())

    def add_invalid_spending(
        self, spend: SpendAdd, category: CategoryDTO, username: str
    ) -> httpx.Response:
        """Добавляет новую невалидную трату."""
        with allure.step("Add invalid spending"):
            payload = spend.model_dump()
            if isinstance(payload.get("spendDate"), datetime):
                payload["spendDate"] = payload["spendDate"].isoformat()
            payload["category"] = category.model_dump()
            payload["username"] = username
            resp = self._post_raw("/api/spends/add", json=payload, headers=self.headers)
            return resp

    def delete_spending(self, ids: list[str]) -> httpx.Response:
        """Удаляет одну или несколько трат по их идентификаторам."""
        with allure.step("Delete spending"):
            resp = self._delete(
                "/api/spends/remove",
                params={"ids": ",".join(ids)},
                headers=self.headers,
            )
            return resp

    def delete_not_exists_spending(self, ids: list[str]) -> httpx.Response:
        """Удаляет одну или несколько несуществующих трат по их идентификаторам."""
        with allure.step("Delete not exists spending"):
            resp = self._delete_raw(
                "/api/spends/remove",
                params={"ids": ",".join(ids)},
                headers=self.headers,
            )
            return resp
