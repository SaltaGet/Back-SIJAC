from datetime import datetime
from enum import Enum
from typing import List
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, Enum as SQLAlchemyEnum
import uuid

from src.config.timezone import get_timezone

class RoleUser(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(SQLModel, table=True):
    __tablename__ = 'users'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(max_length=50)
    email: str = Field(max_length=50, unique=True, index=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    password_hash: str = Field(max_length=100)
    role: str = Field(sa_column=Column(SQLAlchemyEnum(RoleUser)), default=RoleUser.USER)
    specialty: str = Field(max_length=100)
    url_image: str = Field()
    created_at: datetime = Field(default_factory=lambda: get_timezone())
    updated_at: datetime = Field(default_factory=lambda: get_timezone())
    blogs: List["Blog"] = Relationship(back_populates='user')
    availabilities: list["Availability"] = Relationship(back_populates='user')
    appointments: list["Appointment"] = Relationship(back_populates='user')