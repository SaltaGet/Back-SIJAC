from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field, Relationship
from src.config.timezone import get_timezone

class RoomPlan(SQLModel, table= True):
    __tablename__ = 'room_plans'

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key= True, index= True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str = Field(max_length=100)
    cellphone: str = Field(max_length=20)
    tuition: str = Field(max_length=20, unique= True, index= True)
    total_hours: int = Field(default= 0)
    using_hours: int = Field(default= 0)
    created_at: datetime = Field(default_factory=lambda: get_timezone())
    updated_at: datetime = Field(default_factory=lambda: get_timezone())

    room_appointments: list["RoomAppointment"] = Relationship(back_populates='room_plan')