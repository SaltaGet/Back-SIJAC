from pydantic import BaseModel, field_validator
from src.models.case import StateCase


class CaseCreate(BaseModel):
    detail: str
    state: StateCase
    client_id: str

    