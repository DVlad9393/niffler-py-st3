import time
from collections.abc import Sequence

from sqlalchemy import Engine, create_engine, delete, event, func
from sqlmodel import Session, select

from niffler_e_2_e_tests_python.models.user import Friendship, User
from niffler_e_2_e_tests_python.utils.allure_helpers import attach_sql


class UsersDb:
    """Клиент доступа к базе данных пользователей (таблица `user`).

    Инициализирует подключение к БД, предоставляет удобные методы для выборок,
    подсчёта и удаления записей. Для прозрачной отладки SQL-запросы прикрепляются
    в отчёт Allure через обработчик событий SQLAlchemy.

    Особенности:
      • Соединения и транзакции управляются через контекстные менеджеры `Session`.
      • Слушатель `do_execute` добавляет человекочитаемый SQL в Allure-вложения.
      • Методы с `first()` могут вернуть отсутствующее значение, если записи нет.
      • Метод `get_user()` ожидает ровно одну запись и упадёт при 0 или >1 результатах.
    """

    engine: Engine

    def __init__(self, db_url: str):
        """Создаёт подключение к БД и настраивает логирование SQL в Allure.

        :param db_url: Строка подключения к БД в формате SQLAlchemy
                       (например, `postgresql+psycopg2://user:pass@host:5432/dbname`).
        """
        self.engine = create_engine(db_url)
        event.listen(self.engine, "do_execute", fn=attach_sql)

    def get_user(self, username: str) -> Sequence[User]:
        """Возвращает запись пользователя по имени, ожидая ровно один результат.

        Использует `SELECT ... WHERE username = :username` и метод `one()`.
        Если записей нет или найдено больше одной — будет брошено исключение
        SQLAlchemy (`NoResultFound` или `MultipleResultsFound`).

        :param username: Имя пользователя для поиска.
        :return: Единственная найденная запись пользователя.
        """
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            return session.exec(statement).one()

    def get_users(self) -> Sequence[User]:
        """Возвращает все записи пользователей.

        :return: Последовательность объектов пользователей.
        """
        with Session(self.engine) as session:
            statement = select(User)
            return session.exec(statement).all()

    def get_user_by_id(self, user_id) -> User:
        """Возвращает первую найденную запись пользователя по идентификатору.

        Если запись отсутствует, будет возвращено отсутствующее значение.

        :param user_id: Идентификатор пользователя.
        :return: Первая подходящая запись или отсутствующее значение.
        """
        with Session(self.engine) as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).first()

    def get_user_by_username(self, username: str) -> User:
        """Возвращает первую найденную запись пользователя по имени.

        Если запись отсутствует, будет возвращено отсутствующее значение.

        :param username: Имя пользователя для поиска.
        :return: Первая подходящая запись или отсутствующее значение.
        """
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            return session.exec(statement).first()

    def wait_for_user_appears(
        self, username: str, timeout: float = 25.0, poll: float = 0.2
    ) -> User:
        """Ожидает появления пользователя в БД в пределах заданного таймаута.

        Периодически выполняет поиск по имени пользователя с интервалом ожидания.
        Как только запись найдена — возвращает её. Если по истечении времени
        запись так и не появилась, бросает `AssertionError` с диагностикой.

        :param username: Имя пользователя, которого ожидаем.
        :param timeout: Максимальное время ожидания появления записи (в секундах).
        :param poll: Интервал между попытками запроса (в секундах).
        :return: Найденная запись пользователя.
        :raises AssertionError: Если запись не появилась в пределах таймаута.
        """
        deadline = time.time() + timeout
        last_err: Exception | None = None
        while time.time() < deadline:
            try:
                user = self.get_user_by_username(
                    username
                )  # возвращает User или отсутствующее значение
                if user:
                    return user
            except Exception as e:
                last_err = e
            time.sleep(poll)
        raise AssertionError(
            f"user '{username}' not found in DB within {timeout}s; last_err={last_err!r}"
        )

    def count_users_by_username(self, username: str) -> int:
        """Возвращает количество записей с указанным `username`.

        Удобно для проверок идемпотентности и отсутствия дублей.

        :param username: Имя пользователя для подсчёта.
        :return: Число записей в таблице `user` с данным именем.
        """
        with Session(self.engine) as session:
            return session.exec(
                select(func.count()).select_from(User).where(User.username == username)
            ).one()

    def delete_user_by_username(self, username: str) -> None:
        """Удаляет все записи пользователей с указанным `username`.

        Выполняет выборку всех подходящих записей и удаляет их по одной,
        затем фикcирует транзакцию. Полезно для «гигиены» тестовых данных.

        :param username: Имя пользователя, чьи записи нужно удалить.
        :return: Ничего не возвращает.
        """
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            users = session.exec(statement).all()
            for user in users:
                session.delete(user)
            session.commit()

    def delete_user_by_username_from_users_and_friendship(self, username: str) -> None:
        """Удаляет все записи пользователей с указанным `username из таблиц User и Friendship`.

        Выполняет выборку всех подходящих записей и удаляет их по одной,
        затем фикcирует транзакцию. Полезно для «гигиены» тестовых данных.

        :param username: Имя пользователя, чьи записи нужно удалить.
        :return: Ничего не возвращает.
        """
        with Session(self.engine) as session:
            users = session.exec(select(User).where(User.username == username)).all()
            if not users:
                return

            user_ids = [u.id for u in users if u.id]

            if user_ids:
                session.exec(
                    delete(Friendship).where(Friendship.requester_id.in_(user_ids))
                )
                session.exec(
                    delete(Friendship).where(Friendship.addressee_id.in_(user_ids))
                )

            for u in users:
                session.delete(u)

            session.commit()
