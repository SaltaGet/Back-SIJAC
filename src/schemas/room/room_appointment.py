from datetime import date, time
from pydantic import BaseModel

from src.models.room_appointment import StateAppointment


class RoomAppointmentCreate(BaseModel):
  date_get: date 
  first_time: time 
  last_time: time 
  first_name: str | None
  last_name: str | None
  email: str | None
  cellphone: str | None
  tuition: str | None #matricula
  room_availability_id: str
  
class RoomAppointmentUpdate(BaseModel):
  date_get: date 
  first_time: time 
  last_time: time 
  first_name: str | None
  last_name: str | None
  email: str | None
  cellphone: str | None
  tuition: str | None

class RoomAppointmentResponse(BaseModel):
  group_id: str | None
  date_get: date 
  first_time: time 
  last_time: time  
  first_name: str | None
  last_name: str | None
  email: str | None
  cellphone: str | None
  tuition: str | None
  state: StateAppointment

class RoomAppointmentDTO(BaseModel):
  group_id: str | None
  date_get: date 
  first_time: time 
  last_time: time  

