from pydantic import BaseModel, StrictBool, StrictStr
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    """SQL-модель категории трат для базы данных.

    :param id: Уникальный идентификатор категории (primary key).
    :type id: str
    :param name: Название категории.
    :type name: str
    :param username: Имя пользователя, которому принадлежит категория.
    :type username: str
    :param archived: Флаг архивности категории.
    :type archived: bool
    """

    id: str = Field(default=None, primary_key=True)
    name: str
    username: str
    archived: bool = False


class CategoryDTO(BaseModel):
    """DTO-модель категории для передачи данных между слоями приложения.

    :param id: Уникальный идентификатор категории.
    :type id: StrictStr
    :param name: Название категории.
    :type name: StrictStr
    :param username: Имя пользователя, которому принадлежит категория.
    :type username: StrictStr
    :param archived: Флаг архивности категории.
    :type archived: StrictBool
    """

    id: StrictStr
    name: StrictStr
    username: StrictStr
    archived: StrictBool = False
