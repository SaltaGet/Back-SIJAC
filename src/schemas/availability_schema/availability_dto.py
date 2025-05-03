from datetime import date, time
from pydantic import BaseModel

class AvailabilityDto(BaseModel):
    id: str
    date_all: date
    start_time: time
    end_time: time
    start_time_optional: time | None
    end_time_optional: time | None
    disponibility: bool

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if isinstance(v, date) else v,
            time: lambda v: v.isoformat() if isinstance(v, time) else v,
        }