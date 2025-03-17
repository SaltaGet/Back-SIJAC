from datetime import date, time
from pydantic import BaseModel,field_validator

class AppointmentCreate(BaseModel):
    date_get: date
    time_get: time
    full_name: str
    email: str
    cellphone: str
    reason: str
    user_id: int
    availability_id: str

    @field_validator("reason")
    def validate_time(cls, value, values):
        if value > 200:
            raise ValueError("eEl límite es de 200 carácteres para la consulta")
        return value
    
    @field_validator("date_get")
    def validate_date_get(cls, value):
        if value <= date.today():
            raise ValueError("la fecha debe ser posterior debe ser posterior al día de hoy")
        return value