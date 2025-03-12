from datetime import datetime, timezone
from enum import Enum
from typing import List
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, Enum as SQLAlchemyEnum
import uuid

class RoleUser(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(SQLModel, table=True):
    __tablename__ = 'users'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    username: str = Field(max_length=50)
    email: str = Field(max_length=50, unique=True, index=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    password_hash: str = Field(max_length=100)
    role: str = Field(sa_column=Column(SQLAlchemyEnum(RoleUser)), default=RoleUser.USER)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    blogs: List["Blog"] = Relationship(back_populates='user')