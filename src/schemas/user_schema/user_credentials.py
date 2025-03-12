import re
from pydantic import BaseModel, field_validator

class UserCredentials(BaseModel):
    email: str
    password: str

    @field_validator('email')
    def email_validator(cls, email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError('El correo electrónico no es válido')
        return email