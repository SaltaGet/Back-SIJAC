from datetime import datetime

from pydantic import BaseModel
from src.models.case import StateCase
from src.schemas.client.client_response import ClientResponse
from src.schemas.user_schema.user_response import UserResponse


class CaseResponse(BaseModel):
    id: str
    detail: str
    state: StateCase
    client: ClientResponse
    created_at: datetime
    updated_at: datetime
    users: list[UserResponse] = []
