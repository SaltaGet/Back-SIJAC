from datetime import date
from pydantic import BaseModel

class AvailabilityGet(BaseModel):
    id: str
    user_id: str
    date_all: date

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if isinstance(v, date) else v,
        }