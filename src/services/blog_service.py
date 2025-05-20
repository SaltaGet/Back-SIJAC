import base64
import logging
import os
from typing import List
import zlib
from fastapi import HTTPException, Request, status, UploadFile
from src.config.timezone import get_timezone
from src.models.blog_model import Blog
from sqlmodel import desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from src.schemas.blog_schemas.blog_create import BlogCreate
from src.schemas.blog_schemas.blog_response import BlogResponse
from src.schemas.blog_schemas.blog_update import BlogUpdate
from src.schemas.user_schema.user_response import UserResponse
from src.services.image_service import ImageTool


class BlogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.path_image = os.path.join("src", "images", "blog")

    async def create(self, blog: BlogCreate, image: UploadFile):
        try:
            logging.info("Creando blog")
            new_image = await ImageTool(os.path.join('src', 'images', 'blog')).save_image(image)

            if new_image is None:
                return JSONResponse(
                    content={
                        "detail": "Error al guardar la imagen"
                        },
                    status_code=status.HTTP_424_FAILED_DEPENDENCY
                )
            
            new_blog: Blog = Blog(**blog.model_dump(), url_image= new_image)

            self.session.add(new_blog)

            await self.session.commit()

            logging.info("Blog creado!")

            return JSONResponse(
                    content={
                        "blog_id": new_blog.id
                        },
                    status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logging.error(f"Error al crear blog: {e}")
            if new_image:
                ImageTool(os.path.join('src', 'images', 'blog')).delete_image(new_image)
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear el blog")

    async def get_all(self, request: Request, page: int = 1, per_page: int = 9):
        try:
            logging.info("Obteniendo blogs paginados")
            offset = (page - 1) * per_page
            
            sttmt = (
                select(Blog)
                .options(joinedload(Blog.user))
                .order_by(desc(Blog.created_at))
                .limit(per_page)
                .offset(offset)
            )
            
            blogs: List[Blog] = (await self.session.exec(sttmt)).unique().all()

            sttmt_total = select(func.count(Blog.id))
            total_blogs = (await self.session.exec(sttmt_total)).first()
            
            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/image/get_image_blog/"
            
            list_blogs: List[BlogResponse] = []

            for blog in blogs:
                blog.url_image = full_url + blog.url_image if not blog.url_image.startswith("http") else blog.url_image
                if not blog.user.url_image.startswith("http"):
                    blog.user.url_image = f"{scheme}://{host}/image/get_image_user/{blog.user.url_image}"
                user_data = UserResponse.model_validate(blog.user).model_dump(mode='json')
                blog_data = BlogResponse.model_validate(blog).model_dump(mode='json')
                blog_data['user'] = user_data
                list_blogs.append(blog_data)
            
            logging.info("Blogs obtenidos correctamente")
            
            return JSONResponse(
                content={
                    "page": page,
                    "per_page": per_page,
                    "total": len(blogs),
                    "total_pages": (total_blogs // per_page) + 1 if total_blogs > 0 else 0,
                    "data": list_blogs
                },
                status_code=200
            )
        except Exception as e:
            logging.error(f"Error al obtener blogs: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error al intentar obtener los blogs"
            )
        
    async def get(self, request: Request, blog_id: str):
        try:
            logging.info("Obteniendo blog")
            sttmt = select(Blog).options(
                    joinedload(Blog.user)
                ).where(
                    Blog.id == blog_id,
                )
           
            blog: Blog | None = (await self.session.exec(sttmt)).first()

            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/image/get_image_blog/"
            blog.url_image = full_url + blog.url_image if not blog.url_image.startswith("http") else blog.url_image
            
            if blog is None:
                return JSONResponse(
                    content={"detail": "Blog no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            if not blog.user.url_image.startswith("http"):
                blog.user.url_image = f"{scheme}://{host}/image/get_image_user/{blog.user.url_image}"
            user_data = UserResponse.model_validate(blog.user).model_dump(mode='json')
            blog_data = BlogResponse.model_validate(blog).model_dump(mode='json')
            blog_data['user'] = user_data

            logging.info("Blog obtenido")

            return JSONResponse(
                content=blog_data,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener blog: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )
        
    async def update(self, blog: BlogUpdate, image: UploadFile | None, user_id: str):
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
            
            if exist_blog.user_id != user_id:
                return JSONResponse(
                    content={"detail": "No tienes permiso para editar este blog"},
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            exist_blog.title = blog.title
            exist_blog.body = blog.body
            exist_blog.categories = blog.categories
            exist_blog.updated_at = get_timezone()

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
            
            if blog.user_id != blog.user_id:
                return JSONResponse(
                    content={"detail": "No tienes permiso para eliminar este blog"},
                    status_code=status.HTTP_403_FORBIDDEN
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
        
    async def get_last_blogs(self, request: Request):
        try:
            logging.info("Obteniendo blogs paginados")
            sttmt = (
                select(Blog)
                .options(joinedload(Blog.user))
                .order_by(desc(Blog.created_at))
                .limit(3)
                .offset(0)
                )
            
            blogs: List[Blog] = (await self.session.exec(sttmt)).unique().all()

            sttmt_total = select(func.count(Blog.id))
            total_blogs = (await self.session.exec(sttmt_total)).first()
            
            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/image/get_image_blog/"
            
            list_blogs: List[BlogResponse] = []

            for blog in blogs:
                blog.url_image = full_url + blog.url_image if not blog.url_image.startswith("http") else blog.url_image
                if not blog.user.url_image.startswith("http"):
                    blog.user.url_image = f"{scheme}://{host}/image/get_image_user/{blog.user.url_image}"
                user_data = UserResponse.model_validate(blog.user).model_dump(mode='json')
                blog_data = BlogResponse.model_validate(blog).model_dump(mode='json')
                blog_data['user'] = user_data
                list_blogs.append(blog_data)
            
            logging.info("Blogs obtenidos correctamente")
            
            return JSONResponse(
                content={
                    "data": list_blogs
                },
                status_code=200
            )
        except Exception as e:
            logging.error(f"Error al obtener blogs: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error al intentar obtener los blogs"
            )
        
    async def compress_string(self, data):
        compressed = zlib.compress(data.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    
    async def decompress_string(self, compressed_data):
        compressed = base64.b64decode(compressed_data.encode('utf-8'))
        return zlib.decompress(compressed).decode('utf-8')
