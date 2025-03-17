from datetime import date, time
from pydantic import BaseModel,field_validator

class AvailabilityCreate(BaseModel):
    date_all: date
    start_time: time
    end_time: time

    @field_validator("date_all")
    def validate_date_all(cls, value):
        if value <= date.today():
            raise ValueError("date_all debe ser posterior al día de hoy")
        return value
    
    @field_validator("end_time")
    def validate_time(cls, value, values):
        start_time = values.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time debe ser posterior a start_time")
        return value