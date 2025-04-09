from datetime import date, time
from pydantic import BaseModel

from src.models.appointment import StateAppointment

class AppointmentDto(BaseModel):
    id: str
    date_get: date
    start_time: time
    state: StateAppointment

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if isinstance(v, date) else v,
            time: lambda v: v.isoformat() if isinstance(v, time) else v,
        }