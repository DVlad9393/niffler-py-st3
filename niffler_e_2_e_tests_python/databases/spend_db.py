from typing import Sequence

from sqlalchemy import create_engine, Engine
from sqlmodel import Session, select

from niffler_e_2_e_tests_python.models.spend import Category


class SpendDB:

    engine: Engine

    def __init__(self, db_url:str):
        self.engine = create_engine(db_url)

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