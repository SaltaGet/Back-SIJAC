from datetime import datetime
from pydantic import BaseModel

class ClientResponseDTO(BaseModel):
    id: str
    first_name: str
    last_name: str
   