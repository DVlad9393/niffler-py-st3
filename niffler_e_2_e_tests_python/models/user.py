from datetime import date
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


class UserName(BaseModel):
    """Упрощённая модель пользователя для обмена сообщениями.

    Используется как payload при публикации событий в Kafka (например, в топик `users`).

    Поля:
      • username — имя пользователя, уникальный логин/идентификатор в доменной модели.
    """

    username: str


class User(SQLModel, table=True):
    """ORM-модель таблицы `user`, представляющая сущность пользователя системы Niffler.

    Используется в тестах API и при проверках состояния БД.

    Поля:
      • id — первичный ключ записи (строковый UUID или аналогичный идентификатор).
      • username — имя пользователя (уникальный логин, идентификатор в системе).
      • currency — код валюты, выбранной пользователем (по умолчанию "RUB").
      • firstname — имя пользователя.
      • surname — фамилия пользователя.
      • photo — ссылка на оригинальное фото (может быть `None`).
      • photo_small — ссылка на уменьшенную версию фото (может быть `None`).
      • full_name — полное имя пользователя (например, объединённое `firstname + surname`).

    Связи:
      • sent_requests — список исходящих запросов дружбы (связь по `Friendship.requester_id`).
      • received_requests — список входящих запросов дружбы (связь по `Friendship.addressee_id`).

    Эта модель отражает текущее состояние данных пользователей в домене `userdata`.
    """

    __tablename__ = "user"

    id: str = Field(default=None, primary_key=True)
    username: str
    currency: str = "RUB"
    firstname: str
    surname: str
    photo: str | None = None
    photo_small: str | None = None
    full_name: str

    sent_requests: list["Friendship"] = Relationship(
        back_populates="requester",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.requester_id]"},
    )
    received_requests: list["Friendship"] = Relationship(
        back_populates="addressee",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.addressee_id]"},
    )


class Friendship(SQLModel, table=True):
    """ORM-модель таблицы `friendship`, описывающая связи дружбы между пользователями.

    Таблица хранит направление запроса дружбы (`requester_id` → `addressee_id`),
    его текущий статус и дату создания записи.

    Поля:
      • requester_id — идентификатор пользователя, отправившего приглашение (FK → `user.id`).
      • addressee_id — идентификатор пользователя, получившего приглашение (FK → `user.id`).
      • status — текущий статус дружбы (например: `"PENDING"`, `"FRIEND"`, `"VOID"`).
      • created_date — дата создания связи (по умолчанию текущая дата).

    Связи:
      • requester — объект пользователя, инициировавшего запрос дружбы.
      • addressee — объект пользователя, которому было отправлено приглашение.

    Модель используется в тестах SOAP-сценариев (sendInvitation / acceptInvitation /
    declineInvitation) и для проверки корректности состояния таблицы `friendship`
    в базе данных после вызовов API.
    """

    __tablename__ = "friendship"

    requester_id: str = Field(foreign_key="user.id", primary_key=True)
    addressee_id: str = Field(foreign_key="user.id", primary_key=True)
    status: str = Field(default="PENDING", nullable=False)
    created_date: date = Field(default_factory=date.today, nullable=False)

    requester: Optional["User"] = Relationship(
        back_populates="sent_requests",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.requester_id]"},
    )
    addressee: Optional["User"] = Relationship(
        back_populates="received_requests",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.addressee_id]"},
    )
