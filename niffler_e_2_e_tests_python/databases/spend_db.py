import logging
from collections.abc import Sequence

import allure
from sqlalchemy import Engine, create_engine, event
from sqlmodel import Session, select

from niffler_e_2_e_tests_python.models.spend import Category


class SpendDB:
    """Класс для работы с таблицей категорий в базе данных Niffler."""

    engine: Engine

    def __init__(self, db_url: str):
        """Создает подключение к базе данных и настраивает логирование SQL-запросов в Allure.

        :param db_url: URL для подключения к базе данных.
        """
        self.engine = create_engine(db_url)
        event.listen(self.engine, "do_execute", fn=self.attach_sql)

    @staticmethod
    def _pretty_sql(statement: str) -> str:
        """Форматирует SQL-запрос для большей читаемости: переносы строк после ключевых слов.

        :param statement: Текст SQL-запроса.
        :return: SQL-запрос с переносами строк.
        """
        for keyword in [
            "SELECT",
            "FROM",
            "WHERE",
            "ORDER BY",
            "GROUP BY",
            "AND",
            "OR",
            "LEFT JOIN",
            "RIGHT JOIN",
        ]:
            statement = statement.replace(keyword, f"\n{keyword}")
        return statement.strip()

    @staticmethod
    def _safe_format(statement: str, parameters) -> str:
        """Подставляет параметры в SQL для Allure-вложений.
        Не подходит для отправки в базу — только для логов и отчётов!

        :param statement: SQL-запрос с плейсхолдерами.
        :param parameters: Словарь или последовательность с параметрами для подстановки.
        :return: SQL-запрос с подставленными параметрами или исходный запрос при ошибке.
        """
        try:
            if isinstance(parameters, dict):
                params = {
                    k: (f"'{v}'" if isinstance(v, str) else v)
                    for k, v in parameters.items()
                }
                return statement % params

            if isinstance(parameters, tuple | list):
                params = tuple(
                    f"'{v}'" if isinstance(v, str) else v for v in parameters
                )
                return statement % params
        except Exception as e:
            logging.warning(
                f"SQL format error: {e!r}. Statement: {statement}, Params: {parameters}"
            )
        return statement

    @staticmethod
    def attach_sql(cursor, statement, parameters, context) -> None:
        """Добавляет SQL-запрос с параметрами в отчет Allure в читабельном виде.

        :param cursor: Курсор базы данных.
        :param statement: Текст SQL-запроса.
        :param parameters: Параметры для подстановки в SQL.
        :param context: Контекст SQLAlchemy.
        """
        sql = SpendDB._safe_format(statement, parameters)
        pretty_sql = SpendDB._pretty_sql(sql)
        name = f'{statement.split(" ")[0]} {context.engine.url.database}'
        allure.attach(
            pretty_sql, name=name, attachment_type=allure.attachment_type.TEXT
        )

    def get_user_categories(self, username: str) -> Sequence[Category]:
        """Возвращает все категории пользователя.

        :param username: Имя пользователя.
        :return: Список объектов Category.
        """
        with Session(self.engine) as session:
            statement = select(Category).where(Category.username == username)
            return session.exec(statement).all()

    def get_category_by_name(self, name: str) -> Sequence[Category]:
        """Возвращает категории по названию.

        :param name: Название категории.
        :return: Список объектов Category.
        """
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name == name)
            return session.exec(statement).all()

    def delete_category_by_id(self, category_id: str):
        """Удаляет категорию по её идентификатору.

        :param category_id: Идентификатор категории.
        """
        with Session(self.engine) as session:
            category = session.get(Category, category_id)
            session.delete(category)
            session.commit()

    def delete_category_by_name(self, category_name: str):
        """Удаляет все категории с указанным именем.

        :param category_name: Имя категории.
        """
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name == category_name)
            categories = session.exec(statement).all()
            for category in categories:
                session.delete(category)
            session.commit()

    def delete_categories_by_names(self, names: list[str]):
        """Удаляет все категории, имя которых содержится в списке.

        :param names: Список имен категорий.
        """
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name.in_(names))
            categories = session.exec(statement).all()
            for category in categories:
                session.delete(category)
            session.commit()
