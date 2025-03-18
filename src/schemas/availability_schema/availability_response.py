from datetime import date
from pydantic import BaseModel

from src.models.appointment import Appointment
from src.schemas.appointment_schema.appointment_dto import AppointmentDto

class AvailabilityResponseDto(BaseModel):
    id: str
    user_id: str
    date_all: date
    appointments: list[AppointmentDto]

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if isinstance(v, date) else v,
        }