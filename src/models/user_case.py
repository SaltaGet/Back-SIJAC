from datetime import datetime
from enum import Enum
from typing import List
from sqlmodel import Relationship, SQLModel, Field, Text
from sqlalchemy import Column, Enum as SQLAlchemyEnum
import uuid

from src.config.timezone import get_timezone

class TypePermision(str, Enum):
    PRINCIPAL = "pricipal"
    SECONDARY = "secundario"

class UserCase(SQLModel, table=True):
    __tablename__ = 'user_case'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key='users.id')
    case_id: str = Field(foreign_key='cases.id')
    permision: TypePermision = Field(sa_column=Column(SQLAlchemyEnum(TypePermision)), default=TypePermision.SECONDARY)
    created_at: datetime = Field(default_factory=lambda: get_timezone())
    updated_at: datetime = Field(default_factory=lambda: get_timezone())
    case: "Case" = Relationship(back_populates="users")
    user: "User" = Relationship(back_populates="user_cases")