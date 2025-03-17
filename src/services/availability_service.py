import base64
from datetime import date, datetime, timezone
import logging
import os
from typing import List
import zlib
from fastapi import HTTPException, Request, status, UploadFile
from src.models.availability import Availability
from src.models.blog_model import Blog
from sqlmodel import between, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from src.models.user_model import User
from src.schemas.availability_schema.availability_create import AvailabilityCreate
from src.schemas.availability_schema.availability_get import AvailabilityGet
from src.schemas.availability_schema.availability_response import AvailabilityResponse
from src.schemas.blog_schemas.blog_create import BlogCreate
from src.schemas.blog_schemas.blog_response import BlogResponse
from src.schemas.blog_schemas.blog_update import BlogUpdate
from src.schemas.user_schema.user_response import UserResponse
from src.services.image_service import ImageTool


class AvailabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, available: AvailabilityCreate, user: User):
        try:
            logging.info("Creando disponibilidad")
            sttmt_exist = select(Availability).where(Availability.date_all == available.date_all, Availability.user_id == user.id)
            available_exist: Availability | None = (await self.session.exec(sttmt_exist)).first()

            if available_exist is not None:
                return JSONResponse(
                    content={
                        "detail": "Ya existe la disponibilidad del día"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            new_available: Availability = Availability(** available.model_dump(), user_id= user.id,)

            self.session.add(new_available)

            await self.session.commit()

            logging.info("Disponibilidad cread1!")

            return JSONResponse(
                    content={
                        "new_available": new_available.id
                        },
                    status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logging.error(f"Error al crear disponibilidad: {e}")
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear la disponibilidad")

    async def get_all(self, user_id: str, date_start: date = None, date_end: date = None):
        try:
            logging.info("Obteniendo Availabilities")
            if date_start is not None and date_end is not None:
                sttmt = select(Availability).where(
                    between(Availability.date_all, date_start, date_end)
                ).where(Availability.user_id == user_id)
            else: 
                sttmt = select(Availability).where(Availability.user_id == user_id)
           
            availabilities: list[Availability] = (await self.session.exec(sttmt)).all()

            list_availabilities: list[AvailabilityResponse] = [
                AvailabilityResponse(
                    id= avail.id,
                    date_all = avail.date_all,
                    start_time= avail.start_time,
                    end_time= avail.end_time,
                ).model_dump(mode='json')
                for avail in availabilities
            ]
            logging.info("Disponibilidades obtenidas")

            return JSONResponse(
                content= list_availabilities,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener blogs: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )
        
    async def get(self, available_get: AvailabilityGet, ):
        try:
            logging.info("Obteniendo disponibilidad")
            sttmt = select(Availability).options(
                    joinedload(Availability.appointments)
                ).where(
                    Availability.date_all == available_get.date_all,
                    Availability.user_id == available_get.user_id
                )
            
            ##########Continuar aqui
           
            blog: Blog | None = (await self.session.exec(sttmt)).first()

            if blog is None:
                return JSONResponse(
                    content={"detail": "Blog no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            UserResponse.model_validate(blog.user)

            logging.info("Blog obtenido")

            return JSONResponse(
                content=BlogResponse.model_validate(blog).model_dump(mode='json'),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener blog: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )
        
    async def update(self, blog: BlogUpdate, image: UploadFile | None):
        try:
            logging.info("Actualizando blog")
            sttmt = select(Blog).where(
                    Blog.id == blog.id,
                )
           
            exist_blog: Blog | None = (await self.session.exec(sttmt)).first()
            
            if exist_blog is None:
                return JSONResponse(
                    content={"detail": "Blog no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            exist_blog.title = blog.title
            exist_blog.body = blog.body
            exist_blog.categories = blog.categories
            exist_blog.galery = blog.galery
            exist_blog.updated_at = datetime.now(timezone.utc)

            if image is not None:
                image_tool = ImageTool(os.path.join('src', 'images', 'blog'))
                file_name = await image_tool.save_image(image)

                if file_name is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error al intentar editar el blog"
                    )
                
                await image_tool.delete_image(exist_blog.url_image)

                exist_blog.url_image = file_name

            await self.session.commit()

            logging.info("Blog actualizado")
            return JSONResponse(
                content= {'detail': 'Blog editado con exito!'},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al editar blog: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )
        
    async def delete(self, blog_id: str):
        try:
            logging.info("Eliminando blog")
            sttmt = select(Blog).where(Blog.id == blog_id)
            blog: Blog | None = (await self.session.exec(sttmt)).first()
            
            if blog is None:
                return JSONResponse(
                    content={"detail": "Blog no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            await self.session.delete(blog)

            await ImageTool(os.path.join('src', 'images', 'blog')).delete_image(blog.url_image)

            await self.session.commit()

            logging.info("Blog eliminado")

            return JSONResponse(
                content= {"detail": "Blog eliminado con exito!"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al eliminar blog: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar eliminar el blog"
            )
        
    async def get_last_image(self, request: Request):
        try:
            logging.info("Obteniendo ultimas imagenes")
            sttmt = select(Blog.url_image).order_by(Blog.created_at.desc()).where(Blog.galery == True).limit(20)
            images: List[str] = (await self.session.exec(sttmt)).all()

            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/blog/get_image/"

            list_url: List[str] = [full_url+image for image in images]

            logging.info("Imagenes obtenidas")
            
            return JSONResponse(
                content={"images": list_url},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener imagenes")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener las últimas imágenes"
            )
        
    async def compress_string(self, data):
        compressed = zlib.compress(data.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    
    async def decompress_string(self, compressed_data):
        compressed = base64.b64decode(compressed_data.encode('utf-8'))
        return zlib.decompress(compressed).decode('utf-8')
