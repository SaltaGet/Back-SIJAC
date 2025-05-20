from datetime import datetime
from sqlmodel import Relationship, SQLModel, Field
import uuid

from src.config.timezone import get_timezone

class Client(SQLModel, table=True):
    __tablename__ = 'clients'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    dni: str = Field(max_length=20, unique=True, index=True)
    email: str | None= Field(max_length=50)
    phone: str | None = Field()
    created_at: datetime = Field(default_factory=lambda: get_timezone())
    updated_at: datetime = Field(default_factory=lambda: get_timezone())
    cases: list["Case"] = Relationship(back_populates='client')