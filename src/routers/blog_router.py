import os
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database.db import db
from src.models.user_model import User
from src.schemas.blog_schemas.blog_create import BlogCreate
from src.schemas.blog_schemas.blog_update import BlogUpdate
from src.services.auth_service import AuthService
from src.models.blog_model import CategoryBlog
from src.services.blog_service import BlogService
from src.services.image_service import ImageTool

blog_router = APIRouter(prefix='/blog', tags=['Blog'])

auth = AuthService()

############################### POST ###############################

@blog_router.post('/create', status_code= status.HTTP_201_CREATED)
async def create(
    title: str = Form(reqired= True, min_length=1, max_length=100, description='El titulo contener de 3 a 100 carácteres'),
    body: str = Form(reqired= True, min_length=1, description='El cuerpo no puede estar vacio'),
    categories: CategoryBlog = Form(...),
    image: UploadFile = File(...),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    blog: BlogCreate = BlogCreate(title= title, body= body, categories= categories, user_id= user.id)
    return await BlogService(session).create(blog, image)

############################### GET ###############################

@blog_router.get('/get_all')
async def get_all(
    request: Request,
    session: AsyncSession = Depends(db.get_session),
):
    return await BlogService(session).get_all(request)

@blog_router.get('/get/{blog_id}')
async def get(
    request: Request,
    finance_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await BlogService(session).get(request, finance_id, user)

@blog_router.get('get_image/{file_name}')
async def get_image(
    file_name: str,
):
    return await ImageTool(os.path.join('src', 'images', 'blog')).get_image(file_name)

@blog_router.get('/get_last_image')
async def get_last_image(
    request: Request,
    session: AsyncSession = Depends(db.get_session),
):
    return await BlogService(session).get_last_image(request)
############################### PUT ###############################

@blog_router.put('/update/{blog_id}', status_code= status.HTTP_204_NO_CONTENT)
async def update(
    blog_id: str,
    title: str = Form(reqired= True, min_length=1, max_length=100, description='El titulo contener de 3 a 100 carácteres'),
    body: str = Form(reqired= True, min_length=1, description='El cuerpo no puede estar vacio'),
    categories: CategoryBlog = Form(...),
    image: UploadFile | None = File(None),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    blog: BlogUpdate = BlogUpdate(id= blog_id, title= title, body= body, categories= categories, user_id= user.id)
    return await BlogService(session).update(blog, image)

############################### DELETE ###############################

@blog_router.delete('/delete_finance/{finance_id}')
async def delete(
    finance_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await BlogService(session).delete(finance_id, user)

