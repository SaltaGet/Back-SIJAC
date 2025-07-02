from datetime import date, time
from pydantic import BaseModel
from src.schemas.room.room_appointment import RoomAppointmentDTO


class RoomPlanCreate(BaseModel):
  first_name: str
  last_name: str
  email: str
  cellphone: str
  tuition: str 
  
class RoomPlanUpdate(BaseModel):
  first_name: str
  last_name: str
  email: str
  cellphone: str
  tuition: str

class RoomPlanUpdateHours(BaseModel):
  hours: int

class RoomPlanAddAppointmentIds(BaseModel):
  appointment_ids: list[str]
  
class RoomPlanDTO(BaseModel):
  id: str
  first_name: str
  last_name: str
  email: str
  cellphone: str
  tuition: str 
  available_hours: int

  class Config:
      from_attributes = True
      json_encoders = {
          date: lambda v: v.isoformat() if isinstance(v, date) else v,
          time: lambda v: v.isoformat() if isinstance(v, time) else v,
      }

class RoomPlanResponse(BaseModel):
  id: str
  first_name: str
  last_name: str
  email: str
  cellphone: str
  tuition: str 
  available_hours: int
  appointments: list[RoomAppointmentDTO]

  class Config:
      from_attributes = True
      json_encoders = {
          date: lambda v: v.isoformat() if isinstance(v, date) else v,
          time: lambda v: v.isoformat() if isinstance(v, time) else v,
      }



