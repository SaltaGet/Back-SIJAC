from typing import Optional
from pydantic import BaseModel

class EmailContact(BaseModel):
    full_name: str
    cellphone: int
    email: str
    subject: str
    body: str