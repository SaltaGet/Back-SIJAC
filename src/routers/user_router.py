import logging
import traceback
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, logger, status
from fastapi.responses import JSONResponse
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database.db import db
from src.models.user_model import User
from src.schemas.user_schema.user_create import UserCreate
from src.schemas.user_schema.user_credentials import UserCredentials
from src.services.auth_service import AuthService, oauth_scheme
from src.services.user_service import UserService

user_router = APIRouter(prefix='/users', tags=['User'])

auth = AuthService()

############################### POST ###############################

# @user_router.post('/create')
# async def create_user(
#     image: UploadFile = File(...),
#     user: UserCreate,
#     session: AsyncSession = Depends(db.get_session),
# ):
#     return await UserService(session).create_user(user)

@user_router.post('/create')
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password_hash: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    specialty: str = Form(...),
    image: UploadFile = File(...),
    session: AsyncSession = Depends(db.get_session),
):
    try:
        user_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "specialty": specialty
        }

        logging.info(f"Intentando crear usuario con datos: {user_data}")

        try:
            user = UserCreate(**user_data)
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
        return await UserService(session).create_user(user, image)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado. Por favor revise los logs."
        )

@user_router.post('/login')
async def login(
    credentials:UserCredentials,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).login(credentials)

@user_router.post('/logout')
async def login(
    refresh_token: str =  Form(),
    user: User = Depends(auth.get_current_user), 
    session: AsyncSession = Depends(db.get_session),
    token: str = Depends(oauth_scheme),
):
    return await UserService(session).logout(user= user, refresh_token= refresh_token, token= token)

@user_router.post('/refresh_token')
async def refresh_token(
    refresh_token: str =  Form(),
    user: tuple | bool = Depends(auth.get_user_refresh_token), 
    session: AsyncSession = Depends(db.get_session),
):
    if user == False:
        return JSONResponse(
            headers={"WWW-Authenticate": "Bearer"},
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'detail':'Token no caducado'}
        )
    return await UserService(session).refresh_token(user[0], user[1], refresh_token)

############################### GET ###############################

@user_router.get('/me') 
async def user( 
    request: Request,
    user: User = Depends(auth.get_current_user), 
): 
    user_data = user
    scheme = request.scope.get("scheme") 
    host = request.headers.get("host")   
    full_url = f"{scheme}://{host}/image/get_image_user/"
    user_data.url_image= full_url + user_data.url_image
    return user_data

@user_router.get('/validate_email')
async def validate_email(
    email: str,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).validate_email(email)

@user_router.get('/get_users') 
async def get_users( 
    request: Request,
    session: AsyncSession = Depends(db.get_session),
): 
    return await UserService(session).get_users(request)

# ############################### PUT ###############################update_user

@user_router.delete('/reset_tables')
async def reset_tables(
    session: AsyncSession = Depends(db.get_session),
):  
    await session.exec(text("DELETE FROM appointments;"))
    await session.exec(text("DELETE FROM availabilities;"))
    await session.exec(text("DELETE FROM blogs;"))
    await session.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "Tablas reiniciadas"}
    )
