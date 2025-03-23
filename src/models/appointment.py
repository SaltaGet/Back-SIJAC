from datetime import date, datetime, time, timedelta
import uuid
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SQLAlchemyEnum
from sqlalchemy.orm import validates

class StateAppointment(str, Enum):
    CANCEL = "cancelado"
    ACCEPT = "aceptado"
    PENDING = "pendiente"
    REJECT = "rechazado"
    NULL = "nulo"
    RESERVED = "reservado"

class Appointment(SQLModel, table= True):
    __tablename__ = 'appointments'

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key= True, index= True)
    date_get: date = Field()
    start_time: time = Field()
    end_time: time = Field()
    full_name: str | None = Field(max_length=100)
    email: str | None = Field(max_length=100)
    cellphone: str | None = Field(max_length=20)
    reason: str | None = Field(max_length=200)
    state: StateAppointment = Field(sa_column=Column(SQLAlchemyEnum(StateAppointment)), default=StateAppointment.NULL)
    token: str | None = Field(max_length=500, default= None)
    user_id: int = Field(foreign_key="users.id", ondelete= 'CASCADE')
    availability_id: str = Field(foreign_key= 'availabilities.id', ondelete= 'CASCADE')
    user: "User" = Relationship(back_populates='appointments')
    availability: "Availability" = Relationship(back_populates='appointments')
