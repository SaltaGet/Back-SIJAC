from datetime import date, time
from pydantic import BaseModel

class AppointmentDto(BaseModel):
    id: str
    date_get: date
    time_get: time

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if isinstance(v, date) else v,
            time: lambda v: v.isoformat() if isinstance(v, time) else v,
        }