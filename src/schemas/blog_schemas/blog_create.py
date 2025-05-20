from datetime import datetime, timezone
from pydantic import BaseModel, field_validator, model_validator
from src.models.blog_model import CategoryBlog


class BlogCreate(BaseModel):
    title: str
    body: str
    categories: CategoryBlog
    user_id: str
    favorite: bool = False

    @field_validator('title')
    def title_validator(cls, title):
        if len(title.strip()) < 1:
           raise ValueError('El titulo no puede estar vacio')
        return title
    
    @field_validator('body')
    def description_validator(cls, body):
        if len(body.strip()) < 20:
           raise ValueError('El cuerpo no puede estar vacio')
        return body
    