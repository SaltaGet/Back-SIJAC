from datetime import date
from pydantic import BaseModel

class UserUpdate(BaseModel):
    username: str
    first_name: str
    last_name: str