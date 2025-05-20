from datetime import datetime
from pydantic import BaseModel
from src.models.case import StateCase


class CaseResponseDTO(BaseModel):
    id: str
    detail: str
    state: StateCase
    client_id: str
    created_at: datetime
    updated_at: datetime