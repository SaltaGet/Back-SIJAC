from datetime import datetime
from pydantic import BaseModel
from src.models.case import StateCase
from src.schemas.client.client_dto import ClientResponseDTO


class CaseResponseDTO(BaseModel):
    id: str
    detail: str
    state: StateCase
    client: ClientResponseDTO
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }