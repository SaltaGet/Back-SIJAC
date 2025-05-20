from datetime import datetime
from enum import Enum
from typing import List
from sqlmodel import Relationship, SQLModel, Field, Text
from sqlalchemy import Column, Enum as SQLAlchemyEnum
import uuid

from src.config.timezone import get_timezone

class Audit(SQLModel, table=True):
    __tablename__ = 'audits'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key='users.id')
    method: str = Field(max_length=50)
    old_data: str = Field(sa_column=Column(Text))
    new_data: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: get_timezone())
    user: "User" = Relationship(back_populates="audits")
  