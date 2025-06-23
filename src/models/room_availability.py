from datetime import date, time
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel, Relationship

class RoomAvailability(SQLModel, table= True):
    __tablename__ = "room_availabilities"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date_all: date = Field(index= True)
    start_time: time = Field()
    end_time: time = Field()
    room_id: str = Field(foreign_key= 'rooms.id', index= True, ondelete= 'CASCADE')
    room: "Room" = Relationship(back_populates="room_availabilities")
    room_appointments: list["RoomAppointment"] = Relationship(back_populates='room_availability', sa_relationship_kwargs={"cascade": "all, delete-orphan"})