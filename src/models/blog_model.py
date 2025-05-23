from datetime import datetime, timezone
from sqlalchemy import Column, Text
from sqlmodel import Relationship, SQLModel, Field
import uuid
from typing import List
from sqlalchemy import Column, Enum as SQLAlchemyEnum
from enum import Enum

from src.config.timezone import get_timezone

class CategoryBlog(str, Enum):
    ACTIVITIY = "ACTIVIDADES"
    NOTICES = "AVISOS"
    NEWS = "NOTICIAS"
    SEVERAL ="VARIOS"

class Blog(SQLModel, table=True):
    __tablename__ = 'blogs'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    title: str = Field(max_length=100)
    body: str | None = Field(sa_column=Column(Text), default=None)
    url_image: str = Field()
    created_at: datetime = Field(default_factory=lambda: get_timezone())
    updated_at: datetime = Field(default_factory=lambda: get_timezone())
    categories: CategoryBlog = Field(sa_column=Column(SQLAlchemyEnum(CategoryBlog)), default=CategoryBlog.SEVERAL)
    user_id: str = Field(foreign_key='users.id')
    user: "User" = Relationship(back_populates="blogs")
    favorite: bool = Field(default=False)
