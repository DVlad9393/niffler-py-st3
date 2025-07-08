from datetime import datetime

from pydantic import BaseModel, StrictBool, StrictFloat, StrictStr
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


class Spend(SQLModel, table=True):
    """SQL-модель записи о трате для базы данных.

    :param id: Уникальный идентификатор траты (primary key).
    :type id: str
    :param spendDate: Дата и время траты.
    :type spendDate: datetime
    :param category: Идентификатор категории.
    :type category: str
    :param currency: Валюта траты (например, 'RUB').
    :type currency: str
    :param amount: Сумма траты.
    :type amount: float
    :param description: Описание траты.
    :type description: str
    """

    id: str = Field(default=None, primary_key=True)
    spendDate: datetime
    category: str
    currency: str
    amount: float
    description: str


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


class SpendDTO(BaseModel):
    """DTO-модель траты для передачи данных между слоями приложения.

    :param id: Уникальный идентификатор траты.
    :type id: StrictStr
    :param spendDate: Дата и время траты.
    :type spendDate: datetime
    :param category: Категория траты (DTO).
    :type category: CategoryDTO
    :param currency: Валюта траты.
    :type currency: StrictStr
    :param amount: Сумма траты.
    :type amount: StrictFloat
    :param description: Описание траты.
    :type description: StrictStr
    """

    id: StrictStr
    spendDate: datetime
    category: CategoryDTO
    currency: StrictStr
    amount: StrictFloat
    description: StrictStr


class SpendAdd(BaseModel):
    """DTO для создания новой траты.

    :param id: Уникальный идентификатор траты (опционально).
    :type id: StrictStr | None
    :param spendDate: Дата и время траты.
    :type spendDate: datetime
    :param category: Категория траты (DTO).
    :type category: CategoryDTO
    :param currency: Валюта траты.
    :type currency: StrictStr
    :param amount: Сумма траты.
    :type amount: StrictFloat
    :param description: Описание траты.
    :type description: StrictStr
    """

    id: StrictStr | None = None
    spendDate: datetime
    category: CategoryDTO
    currency: StrictStr
    amount: StrictFloat
    description: StrictStr
