from datetime import datetime
from pydantic import BaseModel

from src.models.blog_model import CategoryBlog
from src.schemas.user_schema.user_response import UserResponse


class BlogResponse(BaseModel):
    id: str
    title: str
    body: str
    url_image: str
    categories: CategoryBlog
    favorite: bool
    created_at: datetime
    updated_at: datetime
    user: UserResponse 

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }