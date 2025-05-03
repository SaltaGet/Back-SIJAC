from datetime import date, time
from pydantic import BaseModel,field_validator, model_validator

class AvailabilityCreate(BaseModel):
    date_all: date
    start_time: time
    end_time: time
    start_time_optional: time | None = None
    end_time_optional: time | None = None

    @field_validator("date_all")
    def validate_date_all(cls, value):
        if value <= date.today():
            raise ValueError("date_all debe ser posterior al día de hoy")
        return value
    
    @model_validator(mode= 'before')
    def validate_time(cls, values):
        start_time = values.get("start_time")
        end_time = values.get("end_time")

        start_time_optional = values.get("start_time_optional")
        end_time_optional = values.get("end_time_optional")

        if start_time and end_time <= start_time:
            raise ValueError("end_time debe ser posterior a start_time")
        
        if (start_time_optional is None and end_time_optional is not None) or (start_time_optional is not None and end_time_optional is None):
            raise ValueError("Las horas opcionales deben de estar completas")

        if start_time_optional is not None and end_time_optional is not None:
            if start_time_optional <= end_time:
                raise ValueError("start_time_optional debe ser mayor a end_time")
            if start_time_optional >= end_time_optional:
                raise ValueError("end_time_optional debe ser posterior a start_time_optional")
            # if start_time_optional <= start_time or end_time_optional >= end_time:
            #     raise ValueError("start_time_optional y end_time_optional deben estar dentro del rango de start_time y end_time")

        return values