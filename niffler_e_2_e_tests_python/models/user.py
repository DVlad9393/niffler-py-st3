from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class UserName(BaseModel):
    """Упрощённая модель пользователя для обмена сообщениями.

    Используется как payload при публикации событий в Kafka (например, в топик `users`).

    Поля:
      • username — имя пользователя, уникальный логин/идентификатор в доменной модели.
    """

    username: str


class User(SQLModel, table=True):
    """ORM-модель пользователя для таблицы `user`.

    Предназначена для выборок/проверок в тестах против пользовательской БД.

    Поля:
      • id — первичный ключ записи (строковый идентификатор).
      • username — имя пользователя (логин).
      • currency — код валюты пользователя (например, 'RUB').
      • firstname — имя.
      • surname — фамилия.
      • photo — ссылка на фото (может отсутствовать).
      • photo_small — ссылка на уменьшенную версию фото (может отсутствовать).
      • full_name — полное имя, собранное из частей (или хранимое отдельно).
    """

    id: str = Field(default=None, primary_key=True)
    username: str
    currency: str = "RUB"
    firstname: str
    surname: str
    photo: str | None = None
    photo_small: str | None = None
    full_name: str
