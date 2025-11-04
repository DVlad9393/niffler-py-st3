from __future__ import annotations

import time
from collections.abc import Sequence
from datetime import date

from sqlalchemy import Engine, and_, create_engine, event, func, or_
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlmodel import Session, select

from niffler_e_2_e_tests_python.models.user import Friendship
from niffler_e_2_e_tests_python.utils.allure_helpers import attach_sql


class FriendshipDb:
    """Клиент доступа к БД дружб (таблица `friendship`).

    Предоставляет обёртку над SQLAlchemy/SQLModel для чтения, создания, обновления
    и удаления связей между пользователями. Все SQL-запросы автоматически прикрепляются
    к Allure-отчётам через обработчик событий SQLAlchemy.

    Особенности:
      • Не требует наличия поля `id` — операции строятся по requester_id / addressee_id.
      • Поддерживает ожидание появления связей и массовое удаление по пользователю.
      • Удобен для «гигиены» тестовых данных между SOAP-тестами Userdata.
    """

    engine: Engine

    def __init__(self, db_url: str):
        """Создаёт подключение к базе данных и включает логирование SQL в Allure.

        :param db_url: Строка подключения в формате SQLAlchemy
                       (например, `postgresql+psycopg2://user:pass@host:5432/dbname`).
        """
        self.engine = create_engine(db_url)
        event.listen(self.engine, "do_execute", fn=attach_sql)

    # --------------------
    # SELECT-хелперы
    # --------------------

    def get_all(self) -> Sequence[Friendship]:
        """Возвращает все записи из таблицы `friendship`.

        Используется для отладочных выборок или сверки состояния таблицы.

        :return: Список всех объектов `Friendship`, найденных в таблице.
        """
        with Session(self.engine) as session:
            return session.exec(select(Friendship)).all()

    def get_for_user(self, user_id: str) -> Sequence[Friendship]:
        """Возвращает все связи, где указанный пользователь участвует.

        Выполняет поиск как по requester_id, так и по addressee_id.

        :param user_id: Идентификатор пользователя.
        :return: Список записей дружбы, где пользователь является участником.
        """
        with Session(self.engine) as session:
            stmt = select(Friendship).where(
                or_(
                    Friendship.requester_id == user_id,
                    Friendship.addressee_id == user_id,
                )
            )
            return session.exec(stmt).all()

    def get_between(self, user_a_id: str, user_b_id: str) -> Sequence[Friendship]:
        """Возвращает все связи между двумя пользователями (в обе стороны).

        Полезно для проверки, существует ли дружба между конкретной парой пользователей.

        :param user_a_id: ID первого пользователя.
        :param user_b_id: ID второго пользователя.
        :return: Список найденных записей `Friendship`.
        """
        with Session(self.engine) as session:
            stmt = select(Friendship).where(
                or_(
                    and_(
                        Friendship.requester_id == user_a_id,
                        Friendship.addressee_id == user_b_id,
                    ),
                    and_(
                        Friendship.requester_id == user_b_id,
                        Friendship.addressee_id == user_a_id,
                    ),
                )
            )
            return session.exec(stmt).all()

    def count_for_user(self, user_id: str) -> int:
        """Возвращает количество связей, где участвует пользователь.

        Удобно для валидации, что дружбы были удалены или созданы корректно.

        :param user_id: Идентификатор пользователя.
        :return: Число записей в таблице friendship, связанных с пользователем.
        """
        with Session(self.engine) as session:
            return session.exec(
                select(func.count())
                .select_from(Friendship)
                .where(
                    or_(
                        Friendship.requester_id == user_id,
                        Friendship.addressee_id == user_id,
                    )
                )
            ).one()

    # --------------------
    # WAIT-хелперы
    # --------------------

    def wait_for_link(
        self,
        requester_id: str,
        addressee_id: str,
        status: str | None = None,
        timeout: float = 25.0,
        poll: float = 0.2,
    ) -> Friendship:
        """Ожидает появления связи requester→addressee в таблице `friendship`.

        Периодически выполняет SELECT с указанными параметрами, пока не найдёт запись.
        Если указать `status`, будет ожидать именно такой статус (например, FRIEND).

        :param requester_id: Идентификатор отправителя приглашения.
        :param addressee_id: Идентификатор адресата приглашения.
        :param status: Опциональный фильтр по статусу (PENDING, FRIEND, VOID и т.д.).
        :param timeout: Максимальное время ожидания появления записи, секунд.
        :param poll: Интервал между проверками, секунд.
        :return: Объект `Friendship`, если запись найдена.
        :raises AssertionError: Если запись не появилась за указанный таймаут.
        """
        deadline = time.time() + timeout
        last_err: Exception | None = None
        while time.time() < deadline:
            try:
                with Session(self.engine) as session:
                    conds = [
                        Friendship.requester_id == requester_id,
                        Friendship.addressee_id == addressee_id,
                    ]
                    if status is not None:
                        conds.append(Friendship.status == status)
                    stmt = select(Friendship).where(and_(*conds))
                    row = session.exec(stmt).first()
                    if row:
                        return row
            except Exception as e:
                last_err = e
            time.sleep(poll)
        raise AssertionError(
            f"friendship {requester_id}→{addressee_id} "
            f"{'with status='+status if status else ''} not found within {timeout}s; "
            f"last_err={last_err!r}"
        )

    # --------------------
    # CREATE/UPDATE
    # --------------------

    def create(
        self,
        requester_id: str,
        addressee_id: str,
        status: str = "PENDING",
        created: date | None = None,
    ) -> None:
        """Создаёт новую запись дружбы между пользователями.

        Выполняет INSERT в таблицу friendship. Если запись уже существует,
        поведение зависит от ограничений в БД (обычно выбрасывает ошибку уникальности).

        :param requester_id: ID пользователя, отправившего приглашение.
        :param addressee_id: ID пользователя, которому отправлено приглашение.
        :param status: Статус связи (по умолчанию — 'PENDING').
        :param created: Дата создания записи. Если не указана — используется текущая.
        :return: Ничего не возвращает.
        """
        created = created or date.today()
        with Session(self.engine) as session:
            session.add(
                Friendship(
                    requester_id=requester_id,
                    addressee_id=addressee_id,
                    status=status,
                    created_date=created,
                )
            )
            session.commit()

    def set_status(self, requester_id: str, addressee_id: str, status: str) -> int:
        """Обновляет статус существующей связи requester→addressee.

        Выполняет UPDATE по паре идентификаторов. Если запись не найдена — возвращает 0.

        :param requester_id: ID пользователя, отправившего приглашение.
        :param addressee_id: ID пользователя, которому оно направлено.
        :param status: Новый статус дружбы ('FRIEND', 'VOID', и т.п.).
        :return: Количество затронутых строк.
        """
        with Session(self.engine) as session:
            stmt = (
                sa_update(Friendship)
                .where(
                    and_(
                        Friendship.requester_id == requester_id,
                        Friendship.addressee_id == addressee_id,
                    )
                )
                .values(status=status)
            )
            res = session.exec(stmt)
            session.commit()
            return res.rowcount or 0

    # --------------------
    # DELETE-хелперы
    # --------------------

    def delete_for_user(self, user_id: str) -> int:
        """Удаляет все связи, где пользователь участвует как requester или addressee.

        Используется для очистки данных при удалении тестовых пользователей.

        :param user_id: Идентификатор пользователя, чьи связи нужно удалить.
        :return: Количество удалённых строк.
        """
        with Session(self.engine) as session:
            total = 0
            for cond in (
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id,
            ):
                res = session.exec(sa_delete(Friendship).where(cond))
                total += res.rowcount or 0
            session.commit()
            return total

    def delete_between(self, user_a_id: str, user_b_id: str) -> int:
        """Удаляет все связи между двумя пользователями (в обе стороны).

        Выполняет DELETE для обеих направлений дружбы и возвращает количество удалённых строк.

        :param user_a_id: ID первого пользователя.
        :param user_b_id: ID второго пользователя.
        :return: Количество удалённых строк.
        """
        with Session(self.engine) as session:
            stmt = sa_delete(Friendship).where(
                or_(
                    and_(
                        Friendship.requester_id == user_a_id,
                        Friendship.addressee_id == user_b_id,
                    ),
                    and_(
                        Friendship.requester_id == user_b_id,
                        Friendship.addressee_id == user_a_id,
                    ),
                )
            )
            res = session.exec(stmt)
            session.commit()
            return res.rowcount or 0

    def truncate(self) -> None:
        """Полностью очищает таблицу `friendship`.

        Удаляет все записи без условий. Следует использовать с осторожностью,
        так как это затрагивает все данные в таблице.

        :return: Ничего не возвращает.
        """
        with Session(self.engine) as session:
            session.exec(sa_delete(Friendship))
            session.commit()
