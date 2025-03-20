from datetime import time
from pydantic import BaseModel, field_validator

class AvailabilityUpdate(BaseModel):
    id: str
    start_time: time
    end_time: time

    @field_validator("end_time")
    def validate_time(cls, value, values):
        start_time = values.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time debe ser posterior a start_time")
        return value