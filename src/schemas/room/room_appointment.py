from datetime import date, time
from pydantic import BaseModel

from src.models.room_appointment import StateAppointment


class RoomAppointmentCreate(BaseModel):
  appointment_ids: list[str] 
  first_name: str | None
  last_name: str | None
  email: str | None
  cellphone: str | None
  tuition: str | None 
  # room_availability_id: str
  
class RoomAppointmentUpdate(BaseModel):
  date_get: date 
  first_time: time 
  last_time: time 
  first_name: str | None
  last_name: str | None
  email: str | None
  cellphone: str | None
  tuition: str | None

class RoomAppointmentIds(BaseModel):
  appointment_ids: list[str]
  
class RoomAppointmentDTO(BaseModel):
  id: str
  date_get: date
  start_time: time
  state: StateAppointment
  group_id: str | None

  class Config:
      from_attributes = True
      json_encoders = {
          date: lambda v: v.isoformat() if isinstance(v, date) else v,
          time: lambda v: v.isoformat() if isinstance(v, time) else v,
      }

class RoomAppointmentResponse(BaseModel):
  # id: str
  group_id: str | None
  date_get: date 
  start_time: time 
  end_time: time  
  first_name: str | None
  last_name: str | None
  email: str | None
  cellphone: str | None
  tuition: str | None
  state: StateAppointment
  room_availability_id: str
  appointments: list[RoomAppointmentDTO]

  class Config:
      from_attributes = True
      json_encoders = {
          date: lambda v: v.isoformat() if isinstance(v, date) else v,
          time: lambda v: v.isoformat() if isinstance(v, time) else v,
      }

class RoomAppointmentResponseDTO(BaseModel):
  id: str
  group_id: str | None
  date_get: date 
  start_time: time 
  end_time: time  
  first_name: str | None
  last_name: str | None
  email: str | None
  cellphone: str | None
  tuition: str | None
  state: StateAppointment
  room_availability_id: str

  class Config:
      from_attributes = True
      json_encoders = {
          date: lambda v: v.isoformat() if isinstance(v, date) else v,
          time: lambda v: v.isoformat() if isinstance(v, time) else v,
      }


