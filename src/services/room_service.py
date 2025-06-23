import logging
import os
from fastapi import HTTPException, Request, UploadFile, status
from src.models.room import Room
from src.models.room_appointment import StateAppointment
from src.models.room_availability import RoomAvailability
from src.models.room_image import RoomImage
from sqlmodel import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.room.room import RoomCreate, RoomDTO, RoomResponse, RoomUpdate
from src.schemas.room.room_availability import RoomAvailabilityDTO
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
        logging.info("Actualizando images room")
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
    
  async def update_images(self, room_id: str, images: list[UploadFile]):
    list_images_name: list[str] = [] 
    try:
        logging.info("Actualizando imagenes de room")
        sttmt = select(RoomImage).where(RoomImage.room_id == room_id)
        results: list[RoomImage] = (await self.session.exec(sttmt)).all()

        if len(results) == 0:
            return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        content={"detail": "Room no encontrado"}
                        )

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

        for image in list_images_name:
          self.session.add(RoomImage(room_id=room_id, url_image=image))


        for result in results:
          self.session.delete(result)
          await ImageTool(os.path.join('src', 'images', 'room')).delete_image(result.url_image)

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
        for image in list_images_name:
          await ImageTool(os.path.join('src', 'images', 'room')).delete_image(image)
        await self.session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error al intentar editar room"
        )
        
  async def get(self, request: Request, room_id: str):
    try:
        logging.info("Obteniendo room")
        
        sttmt = (
            select(Room)
            .where(Room.id == room_id)
            .options(
                selectinload(Room.room_images),  # OK: relación directa
                selectinload(Room.room_availabilities).selectinload(RoomAvailability.room_appointments)  # OK: relación anidada
            )
        )
        room: Room | None = (await self.session.exec(sttmt)).unique().first()
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
              RoomAvailabilityDTO(
                id=availability.id,
                date_all=availability.date_all,
                start_time=availability.start_time,
                end_time=availability.end_time,
                disponibility=any(appointment.state == StateAppointment.NULL for appointment in availability.room_appointments) 
              )
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
        if len(rooms) == 0 :
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
        sttmt = select(Room).where(Room.id == room_id).options(selectinload(Room.room_images))
        room: Room | None = (await self.session.exec(sttmt)).first()
        if room is None:
          return JSONResponse(
            content={"detail": "Room no encontrado"},
            status_code=status.HTTP_404_NOT_FOUND
          )
        
        try:
          for image in room.room_images:
            await ImageTool(os.path.join('src', 'images', 'room')).delete_image(image.url_image)
        except Exception as e:
          logging.error(f"Error al eliminar imagen: {e}")
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al intentar elimar imagen de room"
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
    