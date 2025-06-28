from datetime import date, time
import uuid
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SQLAlchemyEnum

class StateAppointment(str, Enum):
    CANCEL = "cancelado"
    ACCEPT = "aceptado"
    PENDING = "pendiente"
    REJECT = "rechazado"
    NULL = "nulo"
    RESERVED = "reservado"

class RoomAppointment(SQLModel, table= True):
    __tablename__ = 'room_appointments'

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key= True, index= True)
    date_get: date = Field()
    start_time: time = Field()
    end_time: time = Field()
    first_name: str | None = Field(max_length=100)
    last_name: str | None = Field(max_length=100)
    email: str | None = Field(max_length=100)
    cellphone: str | None = Field(max_length=20)
    tuition: str | None = Field(max_length=20)
    group_id: str | None = Field(default= None)
    state: StateAppointment = Field(sa_column=Column(SQLAlchemyEnum(StateAppointment)), default=StateAppointment.NULL)
    room_plan_id: str | None = Field(foreign_key="room_plans.id", default= None)
    room_plan: "RoomPlan" = Relationship(back_populates='room_appointments')
    room_id: str = Field(foreign_key="rooms.id", ondelete= 'CASCADE')
    room_availability_id: str = Field(foreign_key= 'room_availabilities.id', ondelete= 'CASCADE')
    room: "Room" = Relationship(back_populates='room_appointments')
    room_availability: "RoomAvailability" = Relationship(back_populates='room_appointments')