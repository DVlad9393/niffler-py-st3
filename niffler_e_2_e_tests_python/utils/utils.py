import os
import dotenv

from httpx import Response
from niffler_e_2_e_tests_python.utils.base_session import BaseSession

dotenv.load_dotenv()

# Можно вынести в глобальные переменные, если нужно
BASE_URL = os.getenv("BASE_URL")

class CategoriesApiClient:
    def __init__(self, session: BaseSession, token: str) -> None:
        self.session = session
        self.token = token

    def get_token(self) -> str:
        return self.token

    def get_all_categories(self, excludeArchived: bool = False) -> Response:
        headers = {'Authorization': f"Bearer {self.get_token()}"}
        return self.session.get(
            "/api/categories/all",
            params={"excludeArchived": excludeArchived},
            headers=headers
        )

    def add_category(self, category_name: str) -> Response:
        payload = {"name": category_name}
        headers = {'Authorization': f"Bearer {self.get_token()}"}
        return self.session.post(
            "/api/categories/add",
            json=payload,
            headers=headers
        )

    def update_category(self, category_id: str, category_name: str, archived: bool) -> Response:
        payload = {
            "id": category_id,
            "name": category_name,
            "archived": archived
        }
        headers = {'Authorization': f"Bearer {self.get_token()}"}
        return self.session.patch(
            "/api/categories/update",
            json=payload,
            headers=headers
        )

class SpendApiClient:
    def __init__(self, session: BaseSession, token: str) -> None:
        self.session = session
        self.token = token

    def get_token(self) -> str:
        return self.token

    def get_all_spends(self, filter_currency: str = None, filter_period: str = None) -> Response:
        headers = {'Authorization': f"Bearer {self.get_token()}"}
        params = {}
        if filter_currency:
            params["filterCurrency"] = filter_currency
        if filter_period:
            params["filterPeriod"] = filter_period
        return self.session.get(
            "/api/spends/all",
            params=params,
            headers=headers
        )

    def add_spending(self, spend: dict) -> Response:
        headers = {'Authorization': f"Bearer {self.get_token()}"}
        return self.session.post(
            "/api/spends/add",
            json=spend,
            headers=headers
        )

    def delete_spending(self, ids: list[str]) -> Response:
        headers = {'Authorization': f"Bearer {self.get_token()}"}
        return self.session.delete(
            "/api/spends/remove",
            params={"ids": ",".join(ids)},
            headers=headers
        )

class UserApiClient:
    def __init__(self, session: BaseSession, token: str) -> None:
        self.session = session
        self.token = token

    def get_token(self) -> str:
        return self.token

    def get_current_user(self) -> Response:
        headers = {'Authorization': f"Bearer {self.get_token()}"}
        return self.session.get("/api/users/current", headers=headers)