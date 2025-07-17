import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import User
from src.schemas.blog_schemas.blog_create import BlogCreate
from src.schemas.blog_schemas.blog_update import BlogUpdate
from src.schemas.room.room import RoomCreate, RoomDTO, RoomResponse, RoomUpdate
from src.services.auth_service import AuthService
from src.models.blog_model import CategoryBlog
from src.services.blog_service import BlogService
from src.services.room_service import RoomService

room_router = APIRouter(prefix='/room', tags=['Room'])

auth = AuthService()

# @authorization(['admin','secretary'])
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

  if not images or len(images) == 0:
        raise HTTPException(status_code=400, detail="Debes subir al menos una imagen.")
  if len(images) > 5:
    raise HTTPException(status_code=400, detail="No puedes subir más de 5 imágenes.")

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

@room_router.get('/get/{room_id}', response_model=RoomResponse)
async def get(
  request: Request,
  room_id: str,
  session: AsyncSession = Depends(db.get_session),
):
  return await RoomService(session).get(request, room_id)

@room_router.get('/get_all', response_model=list[RoomDTO])
async def get_all(
  request: Request,
  session: AsyncSession = Depends(db.get_session),
):
  return await RoomService(session).get_all(request)

# @authorization(['admin','secretary'])
@room_router.put('/update/{room_id}', status_code= status.HTTP_200_OK)
async def update(
  room_id: str,
  room_update: RoomUpdate,
  user: User = Depends(auth.get_current_user),
  session: AsyncSession = Depends(db.get_session),
):
  return await RoomService(session).update(room_id, room_update)

# @authorization(['admin','secretary'])
@room_router.put('/update_images/{room_id}', status_code= status.HTTP_200_OK)
async def update(
  room_id: str,
  images: list[UploadFile],
  user: User = Depends(auth.get_current_user),
  session: AsyncSession = Depends(db.get_session),
):
  if not images or len(images) == 0:
    raise HTTPException(status_code=400, detail="Debes subir al menos una imagen.")
  if len(images) > 5:
    raise HTTPException(status_code=400, detail="No puedes subir más de 5 imágenes.")
  return await RoomService(session).update_images(room_id, images)

# @authorization(['admin','secretary'])
@room_router.delete('/delete/{room_id}', status_code= status.HTTP_200_OK)
async def create_room(
  room_id: str,
  user: User = Depends(auth.get_current_user),
  session: AsyncSession = Depends(db.get_session),
):
  return await RoomService(session).delete(room_id)