from datetime import date, datetime, time
from pydantic import BaseModel

from src.models.blog_model import CategoryBlog
from src.schemas.user_schema.user_response import UserResponse


class AvailabilityResponse(BaseModel):
    id: str
    date_all: date
    start_time: time
    end_time: time

    class Config:
        from_attributes = True
        # json_encoders = {
        #     date: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        # }