# models/spend.py

from datetime import datetime
from pydantic import BaseModel
from sqlmodel import SQLModel, Field

class Category(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    name: str
    username: str
    archived: bool = False

class Spend(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    spendDate: datetime
    category: str
    currency: str
    amount: float
    description: str

class CategoryDTO(BaseModel):
    id: str
    name: str
    username: str
    archived: bool = False

class SpendDTO(BaseModel):
    id: str
    spendDate: datetime
    category: CategoryDTO
    currency: str
    amount: float
    description: str

class SpendAdd(BaseModel):
    id: str | None = None
    spendDate: datetime
    category: CategoryDTO
    currency: str
    amount: float
    description: str