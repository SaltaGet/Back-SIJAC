from datetime import date, time
import uuid
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SQLAlchemyEnum

class StateAppointment(str, Enum):
    CANCEL = "cancelado"
    ACCEPT = "aceptado"
    PENDING = "pendiente"

class Appointment(SQLModel, table= True):
    __tablename__ = 'appointments'

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key= True)
    date_get: date = Field(index= True)
    time_get: time = Field()
    full_name: str = Field(max_length=100)
    email: str = Field(max_length=100)
    cellphone: str = Field(max_length=20)
    reason: str = Field(max_length=200)
    state: StateAppointment = Field(sa_column=Column(SQLAlchemyEnum(StateAppointment)), default=StateAppointment.PENDING)
    user_id: int = Field(foreign_key="users.id")
    availability_id: str = Field(foreign_key= 'availabilities.id')
    user: "User" = Relationship(back_populates='appointments')
    availability: "Availability" = Relationship(back_populates='appointments')