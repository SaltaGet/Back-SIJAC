from datetime import date, time
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel, Relationship

class Availability(SQLModel, table= True):
    __tablename__ = "availabilities"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date_all: date = Field(index= True)
    start_time: time = Field()
    end_time: time = Field()
    user_id: str = Field(foreign_key= 'users.id', index= True)
    user: "User" = Relationship(back_populates="availabilities")
    appointments: list["Appointment"] = Relationship(back_populates='availability')
