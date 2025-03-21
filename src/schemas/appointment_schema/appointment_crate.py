from datetime import date
from pydantic import BaseModel,field_validator

class AppointmentCreate(BaseModel):
    id: str
    full_name: str
    email: str
    cellphone: str
    reason: str

    @field_validator("reason")
    def validate_reason(cls, value):
        if len(value) > 200:
            raise ValueError("El límite es de 200 carácteres para la consulta")
        return value