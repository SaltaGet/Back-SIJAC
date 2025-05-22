from pydantic import BaseModel
from src.models.case import StateCase


class CaseUpdate(BaseModel):
    detail: str
    state: StateCase
