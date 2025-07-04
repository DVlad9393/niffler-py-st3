from pydantic import BaseModel


class Envs(BaseModel):
    api_url: str
    username: str
    password: str
    base_auth_url: str
    base_url: str
    base_error_url: str
    spend_db_url: str