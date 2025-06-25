from httpx import Response
from niffler_e_2_e_tests_python.utils.base_session import BaseSession

class BaseApiClient:
    def __init__(self, session: BaseSession, token: str) -> None:
        self.session = session
        self.set_token(token)

    def set_token(self, token: str) -> None:
        self.token = token
        self.headers = {'Authorization': f"Bearer {self.token}"}

class CategoriesApiClient(BaseApiClient):
    def get_all_categories(self, excludeArchived: bool = False) -> Response:
        resp = self.session.get(
            "/api/categories/all",
            params={"excludeArchived": excludeArchived},
            headers=self.headers
        )
        resp.raise_for_status()
        return resp

    def add_category(self, category_name: str) -> Response:
        payload = {"name": category_name}
        resp = self.session.post(
            "/api/categories/add",
            json=payload,
            headers=self.headers
        )
        resp.raise_for_status()
        return resp

    def update_category(self, category_id: str, category_name: str, archived: bool) -> Response:
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
        resp.raise_for_status()
        return resp


class SpendApiClient(BaseApiClient):
    def get_all_spends(self, filter_currency: str = None, filter_period: str = None) -> Response:
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
        resp.raise_for_status()
        return resp

    def add_spending(self, spend: dict) -> Response:
        resp = self.session.post(
            "/api/spends/add",
            json=spend,
            headers=self.headers
        )
        resp.raise_for_status()
        return resp

    def delete_spending(self, ids: list[str]) -> Response:
        resp = self.session.delete(
            "/api/spends/remove",
            params={"ids": ",".join(ids)},
            headers=self.headers
        )
        resp.raise_for_status()
        return resp


class UserApiClient(BaseApiClient):
    def get_current_user(self) -> Response:
        resp = self.session.get("/api/users/current", headers=self.headers)
        resp.raise_for_status()
        return resp