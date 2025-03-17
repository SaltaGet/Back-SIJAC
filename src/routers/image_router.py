import os
from fastapi import APIRouter
from src.services.image_service import ImageTool

image_router = APIRouter(prefix='/image', tags=['Image'])

@image_router.get('/get/{file_name}')
async def get(
    file_name: str,
):
    return await ImageTool(os.path.join('src', 'images', 'blog')).get_image(file_name)
