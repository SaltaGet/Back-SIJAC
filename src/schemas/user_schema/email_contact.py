from typing import Optional
from pydantic import BaseModel

class EmailContact(BaseModel):
    subject: str
    body: str
    to_email: str
    from_email: Optional[str]