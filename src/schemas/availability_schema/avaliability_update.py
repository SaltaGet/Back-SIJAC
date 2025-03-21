from datetime import time
from pydantic import BaseModel, model_validator

class AvailabilityUpdate(BaseModel):
    start_time: time
    end_time: time

    @model_validator(mode= 'before')
    def validate_time(cls, values):
        start_time = values.get("start_time")
        end_time = values.get("end_time")

        if start_time and end_time <= start_time:
            raise ValueError("end_time debe ser posterior a start_time")
        return values