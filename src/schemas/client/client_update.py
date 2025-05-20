from pydantic import BaseModel

class ClientUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    

