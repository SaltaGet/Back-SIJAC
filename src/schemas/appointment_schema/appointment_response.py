from pydantic import BaseModel
from datetime import date, time

from src.models.appointment import StateAppointment

class AppointmentResponse(BaseModel):
    id: str
    date_get: date
    start_time: time
    end_time: time
    full_name: str | None
    email: str | None
    cellphone: str | None
    reason: str | None
    state: StateAppointment
    user_id: str
    availability_id: str

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if isinstance(v, date) else v,
            time: lambda v: v.isoformat() if isinstance(v, time) else v,
        }
