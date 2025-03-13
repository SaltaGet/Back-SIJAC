import base64
from datetime import datetime, timezone
import os
from typing import List
import zlib
from fastapi import HTTPException, Request, status, UploadFile
from src.models.blog_model import Blog
from sqlmodel import select
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

            return JSONResponse(
                    content={
                        "blog_id": new_blog.id
                        },
                    status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            if new_image:
                ImageTool(os.path.join('src', 'images', 'blog')).delete_image(new_image)
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear el blog")

    async def get_all(self, request: Request):
        try:
            sttmt = select(Blog).options(
                    joinedload(Blog.user)
                )
           
            blogs: List[Blog] = (await self.session.exec(sttmt)).all()

            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/blog/get_image/"
            
            list_blogs: List[BlogResponse] = [
                BlogResponse(
                    id= blog.id,
                    title= blog.title,
                    body= blog.body,
                    categories= blog.categories,
                    galery= blog.galery,
                    url_image= full_url+blog.url_image,
                    created_at= blog.created_at.isoformat(),
                    updated_at= blog.updated_at.isoformat(),
                    user = UserResponse.model_validate(blog.user)
                ).model_dump(mode='json')
                for blog in blogs
            ]

            return JSONResponse(
                content= list_blogs,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )
        
    async def get(self, request: Request, blog_id: str):
        try:
            sttmt = select(Blog).options(
                    joinedload(Blog.user)
                ).where(
                    Blog.id == blog_id,
                )
           
            blog: Blog | None = (await self.session.exec(sttmt)).first()

            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/blog/get_image/"
            blog.url_image = full_url+blog.url_image
            
            if blog is None:
                return JSONResponse(
                    content={"detail": "Blog no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            UserResponse.model_validate(blog.user)

            return JSONResponse(
                content={"blog": BlogResponse.model_validate(blog)},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )
        
    async def update(self, blog: BlogUpdate, image: UploadFile | None):
        try:
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
                file_name = image_tool.save_image(image)

                if file_name is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error al intentar editar el blog"
                    )
                
                await image_tool.delete_image(exist_blog.url_image)

                exist_blog.url_image = file_name

            self.session.commit()
            return JSONResponse(
                content={},
                status_code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )
        
    async def delete(self, blog_id: str):
        try:
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

            return JSONResponse(
                content= {"detail": "Blog eliminado con exito!"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar eliminar el blog"
            )
        
    async def get_last_image(self, request: Request):
        try:
            sttmt = select(Blog.url_image).order_by(Blog.created_at.desc()).where(Blog.galery == True).limit(20)
            images: List[str] = (await self.session.exec(sttmt)).all()

            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/blog/get_image/"

            list_url: List[str] = [full_url+image for image in images]
            
            return JSONResponse(
                content={"images": list_url},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
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
