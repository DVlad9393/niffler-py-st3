from datetime import datetime

import allure
import httpx
from niffler_e_2_e_tests_python.models.spend import CategoryDTO, SpendDTO, SpendAdd
from niffler_e_2_e_tests_python.utils.base_session import BaseSession

class BaseApiClient:
    def __init__(self, session: BaseSession, token: str) -> None:
        """
        Инициализирует API клиент с сессией и токеном авторизации.

        :param session: Экземпляр сессии для выполнения HTTP-запросов.
        :param token: JWT-токен для авторизации.
        """
        self.session = session
        self.set_token(token)

    def set_token(self, token: str) -> None:
        """
        Устанавливает токен авторизации для последующих запросов.

        :param token: JWT-токен для авторизации.
        """
        with allure.step("Set token"):
            self.token = token
            self.headers = {'Authorization': f"Bearer {self.token}"}

    @staticmethod
    def raise_for_status(resp: httpx.Response):
        """
        Проверяет статус ответа и выбрасывает исключение, если произошла ошибка.

        :param resp: Ответ httpx.Response от сервера.
        :raises httpx.HTTPStatusError: Если статус ответа не 200 или 201.
        """
        with allure.step("Check status"):
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 200 and e.response.status_code != 201:
                    e.add_note(resp.text)
                    raise e

class CategoriesApiClient(BaseApiClient):
    def get_all_categories(self, excludeArchived: bool = False) -> list[CategoryDTO]:
        """
        Получает список всех категорий пользователя.

        :param excludeArchived: Исключать ли архивированные категории (по умолчанию False).
        :return: Список объектов CategoryDTO.
        """
        with allure.step("Get all categories"):
            resp = self.session.get(
                "/api/categories/all",
                params={"excludeArchived": excludeArchived},
                headers=self.headers
            )
            self.raise_for_status(resp)
            return [CategoryDTO.model_validate(item) for item in resp.json()]

    def add_category(self, category_name: str) -> CategoryDTO:
        """
        Создаёт новую категорию.

        :param category_name: Название новой категории.
        :return: Созданная категория как CategoryDTO.
        """
        with allure.step("Add category"):
            payload = {"name": category_name}
            resp = self.session.post(
                "/api/categories/add",
                json=payload,
                headers=self.headers
            )
            self.raise_for_status(resp)
            return CategoryDTO.model_validate(resp.json())

    def update_category(self, category_id: str, category_name: str, archived: bool) -> CategoryDTO:
        """
        Обновляет существующую категорию (например, название или признак архивации).

        :param category_id: ID категории.
        :param category_name: Новое имя категории.
        :param archived: Статус архивации (True/False).
        :return: Обновлённая категория как CategoryDTO.
        """
        with allure.step("Update category"):
            payload = {
                "id": category_id,
                "name": category_name,
                "archived": archived
            }
            resp = self.session.patch(
                "/api/categories/update",
                json=payload,
                headers=self.headers
            )
            self.raise_for_status(resp)
            return CategoryDTO.model_validate(resp.json())

class SpendApiClient(BaseApiClient):
    def get_all_spends(self, filter_currency: str = None, filter_period: str = None) -> list[SpendDTO]:
        """
        Получает список всех трат пользователя с возможностью фильтрации.

        :param filter_currency: Фильтр по валюте (например, 'RUB').
        :param filter_period: Фильтр по периоду (например, 'month', 'week').
        :return: Список объектов SpendDTO.
        """
        with allure.step("Get all spends"):
            params = {}
            if filter_currency:
                params["filterCurrency"] = filter_currency
            if filter_period:
                params["filterPeriod"] = filter_period
            resp = self.session.get(
                "/api/spends/all",
                params=params,
                headers=self.headers
            )
            self.raise_for_status(resp)
            return [SpendDTO.model_validate(item) for item in resp.json()]

    def add_spending(self, spend: SpendAdd, category: CategoryDTO, username: str) -> SpendDTO:
        """
        Добавляет новую трату.

        :param spend: Данные траты (SpendAdd).
        :param category: Категория, к которой относится трата (CategoryDTO).
        :param username: Имя пользователя, для которого добавляется трата.
        :return: Добавленная трата как SpendDTO.
        """
        with allure.step("Add spending"):
            payload = spend.model_dump()
            if isinstance(payload.get("spendDate"), datetime):
                payload["spendDate"] = payload["spendDate"].isoformat()
            payload["category"] = category.model_dump()
            payload["username"] = username
            resp = self.session.post(
                "/api/spends/add",
                json=payload,
                headers=self.headers
            )
            self.raise_for_status(resp)
            return SpendDTO.model_validate(resp.json())

    def delete_spending(self, ids: list[str]) -> None:
        """
        Удаляет одну или несколько трат по их идентификаторам.

        :param ids: Список идентификаторов трат для удаления.
        """
        with allure.step("Delete spending"):
            resp = self.session.delete(
                "/api/spends/remove",
                params={"ids": ",".join(ids)},
                headers=self.headers
            )
            self.raise_for_status(resp)