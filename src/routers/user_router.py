from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse
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

@user_router.post('/create')
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).create_user(user)

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
    user: User = Depends(auth.get_current_user), 
): 
    user_data = user
    return user_data

@user_router.get('/validate_email')
async def validate_email(
    email: str,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).validate_email(email)

# ############################### PUT ###############################update_user

