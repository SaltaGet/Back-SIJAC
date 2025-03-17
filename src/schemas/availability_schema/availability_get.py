from datetime import date, time
from pydantic import BaseModel,field_validator

class AvailabilityGet(BaseModel):
    user_id: str
    date_all: date