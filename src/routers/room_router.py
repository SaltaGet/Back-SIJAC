import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import User
from src.schemas.blog_schemas.blog_create import BlogCreate
from src.schemas.blog_schemas.blog_update import BlogUpdate
from src.schemas.room.room import RoomCreate
from src.services.auth_service import AuthService
from src.models.blog_model import CategoryBlog
from src.services.blog_service import BlogService
from src.services.room_service import RoomService

room_router = APIRouter(prefix='/room', tags=['Room'])

auth = AuthService()

@authorization(['admin','secretary'])
@room_router.post('/create')
async def create_room(
  name: str = Form(...),
  type_room: str = Form(...),
  description: str = Form(...),
  price: float = Form(...),
  images: list[UploadFile] = File(...),
  user: User = Depends(auth.get_current_user),
  session: AsyncSession = Depends(db.get_session),
):
  room_data = {
      "name": name,
      "type_room": type_room,
      "description": description,
      "price": price,
  }

  logging.info(f"Intentando crear room con datos: {room_data}")

  try:
      room = RoomCreate(**room_data)
  except ValueError as e:
      logging.error(f"Error de validación: {str(e)}")
      raise HTTPException(
          status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
          detail=str(e)
      )
  except Exception as e:
      logging.error(f"Error inesperado al validar: {str(e)}")
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=f"Error en los datos del usuario: {str(e)}"
      )
  return await RoomService(session).create(room, images)