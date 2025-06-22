from datetime import date, timedelta
import logging
import os
import bcrypt
from fastapi import HTTPException, Request, UploadFile, status
from src.config.timezone import get_timezone
from src.models.refresh_token import HistorialRefreshToken
from src.models.room import Room
from src.models.room_image import RoomImage
from src.models.user_model import RoleUser, User
from sqlmodel import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.room.room import RoomCreate, RoomDTO, RoomResponse, RoomUpdate
from src.schemas.room.room_availability import RoomAvailabilityResponse
from src.schemas.user_schema.user_create import UserCreate
from src.schemas.user_schema.user_credentials import UserCredentials
from src.schemas.user_schema.user_response import UserResponse
from src.schemas.user_schema.user_update import UserUpdate
from src.services.auth_service import AuthService
from src.services.image_service import ImageTool

class RoomService:
  def __init__(self, session: AsyncSession = None):
    self.session = session

  async def create(self, room_create: RoomCreate, images: list[UploadFile]):
    try:
        logging.info("Creando room")

        list_images_name: list[str] = [] 
        if len(images) > 0:
          for image in images:
            new_image = await ImageTool(os.path.join('src', 'images', 'room')).save_image(image)
            if new_image is None:
                return JSONResponse(
                    content={
                        "detail": "Error al guardar la imagen"
                        },
                    status_code=status.HTTP_424_FAILED_DEPENDENCY
                )
            list_images_name.append(new_image)

        new_room = Room(**room_create.model_dump())
        self.session.add(new_room)
        await self.session.flush()

        for image in list_images_name:
          self.session.add(RoomImage(room_id=new_room.id, url_image=image))

        await self.session.commit()

        logging.info("Room creado!")
        return JSONResponse(
            content={
                "room_id": new_room.id
                },
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logging.error(f"Error al crear room: {e}")
        await self.session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error al intentar crear room"
        )
  
  async def update(self, room_id: str, room_update: RoomUpdate):
    try:
        logging.info("Actualizando room")
        result: Room = await self.session.get(Room, room_id)

        if result is None:
            return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        content={"detail": "Room no encontrado"}
                        )

        result.name = room_update.name
        result.type_room = room_update.type_room
        result.description = room_update.description
        result.price = room_update.price

        await self.session.commit()

        logging.info("Room actualizado!")
        return JSONResponse(
            content={
                "detail": "Room actualizado con exito"
                },
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logging.error(f"Error al editar room: {e}")
        await self.session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error al intentar editar room"
        )
        
  async def get(self, request: Request, room_id: str):
    try:
        logging.info("Obteniendo room")
        sttmt = select(Room).where(Room.id == room_id).options(selectinload(Room.room_images), selectinload(Room.room_appointments))
        room: Room | None = (await self.session.exec(sttmt)).first()
        if room is None:
          return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, 
            content={"detail": "Room no encontrado"}
          )
        
        scheme = request.scope.get("scheme") 
        host = request.headers.get("host")   
        full_url = f"{scheme}://{host}/image/get_image_room/"
        
        room_response = RoomResponse(
          id=room.id,
          name=room.name,
          type_room=room.type_room,
          description=room.description,
          price=room.price,
          created_at=room.created_at,
          url_image=[full_url + img.url_image for img in room.room_images],
          availabilities=[
              RoomAvailabilityResponse.model_validate(availability)
              for availability in room.room_availabilities
          ]
        )

        logging.info("Room obtenido")
      
        return JSONResponse(
            content= room_response.model_dump(mode='json'),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error(f"Error al obtener room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al intentar obtener el room"
        )
      
  async def get_all(self, request: Request):
    try:
        logging.info("Obteniendo rooms")
        sttmt = select(Room).options(selectinload(Room.room_images))
        rooms: list[Room] = (await self.session.exec(sttmt)).all()
        if len(room) == 0 :
          return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content= []
          )
        
        scheme = request.scope.get("scheme") 
        host = request.headers.get("host")   
        full_url = f"{scheme}://{host}/image/get_image_room/"
        
        list_rooms = []
        for room in rooms:
          room_response = RoomDTO(
              id=room.id,
              name=room.name,
              type_room=room.type_room,
              description=room.description,
              price=room.price,
              created_at=room.created_at,
              url_image=[full_url + img.url_image for img in room.room_images]
          ).model_dump(mode='json')
          list_rooms.append(room_response)

        logging.info("Rooms obtenido")
      
        return JSONResponse(
            content= list_rooms,
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error(f"Error al obtener rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al intentar obtener rooms"
        )
    
  async def delete(self, room_id: str):
    try:
        logging.info("Eliminando room")
        # sttmt = select(Room).where(Room.id == room_id).options(selectinload(Room.room_images), selectinload(Room.room_appointments))
        # room: Room | None = (await self.session.exec(sttmt)).first()
        # if room is None:
        #   return JSONResponse(
        #     status_code=status.HTTP_404_NOT_FOUND, 
        #     content={"detail": "Room no encontrado"}
        #   )

        # for appointment in room.room_appointments:
        #   await self.session.delete(appointment)
        
        # try:
        #   for image in room.room_images:
        #     await ImageTool(os.path.join('src', 'images', 'room')).delete_image(image.url_image)
        # except Exception as e:
        #   logging.error(f"Error al eliminar imagen: {e}")
        #   raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     detail="Error al intentar elimar imagen de room"
        #   )

        sttmt = select(Room).where(Room.id == room_id)
        room: Room | None = (await self.session.exec(sttmt)).first()
        if room is None:
          return JSONResponse(
            content={"detail": "Room no encontrado"},
            status_code=status.HTTP_404_NOT_FOUND
          )

        await self.session.delete(room)
        await self.session.commit()

        logging.info("Room eliminado!")
        return JSONResponse(
            content={
                "detail": "Room eliminado con exito"
                },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
      logging.error(f"Error al eliminar room: {e}")
      await self.session.rollback()
      raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al intentar eliminar room"
        )
    