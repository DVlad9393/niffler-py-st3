from datetime import datetime

from pydantic import BaseModel, StrictFloat, StrictStr
from sqlmodel import Field, SQLModel

from niffler_e_2_e_tests_python.models.category import CategoryDTO


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


class SpendDTO(BaseModel):
    """DTO-модель траты для передачи данных между слоями приложения.

    :param id: Уникальный идентификатор траты.
    :type id: StrictStr
    :param spendDate: Дата и время траты.
    :type spendDate: datetime
    :param category: Категория траты (DTO).
    :type category: niffler_e_2_e_tests_python.models.category.CategoryDTO
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
