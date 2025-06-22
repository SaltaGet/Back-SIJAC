from datetime import datetime
from sqlalchemy import Column, Text
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column
import uuid

from src.config.timezone import get_timezone

class Room(SQLModel, table=True):
  __tablename__ = 'rooms'
  id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
  name: str = Field(max_length=100)
  type_room: str = Field(max_length=100)
  description: str = Field(sa_column=Column(Text), default=None)
  price: float = Field()
  created_at: datetime = Field(default_factory=lambda: get_timezone())
  updated_at: datetime = Field(default_factory=lambda: get_timezone())
  room_availabilities: list["RoomAvailability"] = Relationship(
  back_populates="room",
      sa_relationship_kwargs={"cascade": "all, delete-orphan"}
  )
  room_appointments: list["RoomAppointment"] = Relationship(
      back_populates="room",
      sa_relationship_kwargs={"cascade": "all, delete-orphan"}
  )
  room_images: list["RoomImage"] = Relationship(
      back_populates="room",
      sa_relationship_kwargs={"cascade": "all, delete-orphan"}
  )
    # room_availabilities: list["RoomAvailability"] = Relationship(back_populates='room')
    # room_appointments: list["RoomAppointment"] = Relationship(back_populates='room')
    # room_images: list["RoomImage"] = Relationship(back_populates="room")