from datetime import date, datetime, time
from typing import Optional
from pydantic import BaseModel

from src.schemas.room.room_appointment import RoomAppointmentDTO, RoomAppointmentResponse


class RoomAvailabilityCreate(BaseModel):
  date_all: date
  start_time: time
  end_time: time 
  start_time_optional: time | None
  end_time_optional: time | None
  room_id: str


class RoomAvailabilityUpdate(BaseModel):
  start_time: time
  end_time: time 
  start_time_optional: time | None
  end_time_optional: time | None

class RoomAvailabilityDTO(BaseModel):
  id: str
  date_all: date
  start_time: time
  end_time: time
  start_time_optional: time | None
  end_time_optional: time | None
  disponibility: bool
  appointments: list[RoomAppointmentDTO]

  class Config:
    orm_mode = True
    json_encoders = {
      datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
    }

class RoomAvailabilityResponse(BaseModel):
  id: str
  date_all: date
  start_time: time
  end_time: time
  start_time_optional: time | None
  end_time_optional: time | None
  appointments: list[RoomAppointmentDTO]

  class Config:
    orm_mode = True
    json_encoders = {
      datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
    }

