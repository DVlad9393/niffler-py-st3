from typing import Sequence

import allure
from sqlalchemy import create_engine, Engine, event
from sqlmodel import Session, select

from niffler_e_2_e_tests_python.models.spend import Category


class SpendDB:

    engine: Engine

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        event.listen(self.engine, 'do_execute', fn=self.attach_sql)

    @staticmethod
    def _pretty_sql(statement: str) -> str:
        """
        Форматирует SQL-запрос для большей читаемости: переносы строк после ключевых слов.
        """
        for keyword in ["SELECT", "FROM", "WHERE", "ORDER BY", "GROUP BY", "AND", "OR", "LEFT JOIN", "RIGHT JOIN"]:
            statement = statement.replace(keyword, f"\n{keyword}")
        return statement.strip()

    @staticmethod
    def _safe_format(statement: str, parameters) -> str:
        """
        Подставляет параметры в SQL для Allure-вложений.
        Не подходит для отправки в базу — только для логов и отчётов!
        """
        try:
            # dict params: statement with %(name)s
            if isinstance(parameters, dict):
                # Кавычки для строк
                params = {k: (f"'{v}'" if isinstance(v, str) else v) for k, v in parameters.items()}
                return statement % params
            # tuple/list params: statement with %s
            if isinstance(parameters, (tuple, list)):
                params = tuple(f"'{v}'" if isinstance(v, str) else v for v in parameters)
                return statement % params
        except Exception:
            pass
        return statement

    @staticmethod
    def attach_sql(cursor, statement, parameters, context) -> None:
        """
        Добавляет SQL-запрос с параметрами в отчёт Allure в читабельном виде.
        """
        sql = SpendDB._safe_format(statement, parameters)
        pretty_sql = SpendDB._pretty_sql(sql)
        name = f"{statement.split(' ')[0]} {context.engine.url.database}"
        allure.attach(
            pretty_sql,
            name=name,
            attachment_type=allure.attachment_type.TEXT
        )

    def get_user_categories(self, username: str) -> Sequence[Category]:
        with Session(self.engine) as session:
            statement = select(Category).where(Category.username == username)
            return session.exec(statement).all()

    def get_category_by_name(self, name: str) -> Sequence[Category]:
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name == name)
            return session.exec(statement).all()

    def delete_category_by_id(self, category_id: str):
        with Session(self.engine) as session:
            category = session.get(Category, category_id)
            session.delete(category)
            session.commit()

    def delete_category_by_name(self, category_name: str):
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name == category_name)
            categories = session.exec(statement).all()
            for category in categories:
                session.delete(category)
            session.commit()

    def delete_categories_by_names(self, names: list[str]):
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name.in_(names))
            categories = session.exec(statement).all()
            for category in categories:
                session.delete(category)
            session.commit()