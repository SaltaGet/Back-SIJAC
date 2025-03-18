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

class Appointment(SQLModel, table= True):
    __tablename__ = 'appointments'

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key= True)
    date_get: date = Field(index= True)
    start_time: time = Field()
    end_time: time = Field(default= None)
    full_name: str = Field(max_length=100)
    email: str = Field(max_length=100)
    cellphone: str = Field(max_length=20)
    reason: str = Field(max_length=200)
    state: StateAppointment = Field(sa_column=Column(SQLAlchemyEnum(StateAppointment)), default=StateAppointment.PENDING)
    user_id: int = Field(foreign_key="users.id")
    availability_id: str = Field(foreign_key= 'availabilities.id')
    user: "User" = Relationship(back_populates='appointments')
    availability: "Availability" = Relationship(back_populates='appointments')

    @validates("start_time")
    def set_end_time(self, key, start_time):
        """ Calcula y almacena end_time basado en start_time """
        dt = datetime.combine(datetime.today(), start_time) + timedelta(minutes=45)
        self.end_time = dt.time()
        return start_time