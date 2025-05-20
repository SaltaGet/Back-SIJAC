from datetime import datetime
from enum import Enum
from typing import List
from sqlmodel import Relationship, SQLModel, Field, Text
from sqlalchemy import Column, Enum as SQLAlchemyEnum
import uuid

from src.config.timezone import get_timezone

class StateCase(str, Enum):
    CANCEL = "cancelado"
    PENDING = "pendiente"
    INITIAL = "iniciado"
    PROCESS = "tramitado"
    FINISH = "finalizado"
    NULL = "nulo"

class Case(SQLModel, table=True):
    __tablename__ = 'cases'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    detail: str = Field(sa_column=Column(Text))
    state: StateCase = Field(sa_column=Column(SQLAlchemyEnum(StateCase)), default=StateCase.NULL)
    created_at: datetime = Field(default_factory=lambda: get_timezone())
    updated_at: datetime = Field(default_factory=lambda: get_timezone())
    client_id: str = Field(foreign_key='clients.id')
    client: "Client" = Relationship(back_populates="cases")
    users: list["UserCase"] = Relationship(back_populates="user")