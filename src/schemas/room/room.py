from datetime import datetime
from pydantic import BaseModel

from src.schemas.room.room_availability import RoomAvailabilityDTO

class RoomCreate(BaseModel):
  name: str
  type_room: str
  description: str
  price: float


class RoomUpdate(BaseModel):
  name: str
  type_room: str
  description: str
  price: float


class RoomResponse(BaseModel):
  id: str
  name: str
  type_room: str
  description: str
  price: float
  url_image: list[str]
  availabilities: list[RoomAvailabilityDTO]
  created_at: datetime

  class Config:
    orm_mode = True
    json_encoders = {
      datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
    }

class RoomDTO(BaseModel):
  id: str
  name: str
  type_room: str
  description: str
  price: float
  url_image: list[str]
  created_at: datetime

  class Config:
    orm_mode = True
    json_encoders = {
      datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
    }
