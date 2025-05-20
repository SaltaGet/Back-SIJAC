from datetime import datetime
from pydantic import BaseModel

class ClientResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    dni: str
    email: str
    phone: str
    created_at: datetime
    updated_at: datetime
