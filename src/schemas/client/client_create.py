from pydantic import BaseModel

class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    dni: str
    email: str
    phone: str
