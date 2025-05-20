from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database.db import db
from src.models.user_model import User
from src.schemas.client.client_create import ClientCreate
from src.schemas.client.client_update import ClientUpdate
from src.services.client_service import ClientService
from src.services.auth_service import AuthService


client_router = APIRouter(prefix='/client', tags=['Client'])

auth = AuthService()

############################### GET ###############################

@client_router.get('/get_all')
async def get_all(
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
  return await ClientService(session).get_all(user.id)

@client_router.get('/get/{client_id}')
async def get(
    client_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ClientService(session).get(client_id, user.id)

@client_router.get('/get_by_dni/{dni}')
async def get_by_dni(
    dni: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
  return await ClientService(session).get_by_dni(dni, user.id)

@client_router.get('/get_by_name')
async def get_by_name(
    name: str = Query(..., min_length=3, max_length=100),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
  return await ClientService(session).get_by_name(name, user.id)

############################### PUT ###############################

@client_router.put('/update/{client_id}', status_code= status.HTTP_200_OK)
async def update(
    client_id: str,
    client_update: ClientUpdate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ClientService(session).update(client_id, client_update, user.id)

############################### POST ###############################

@client_router.post('/create', status_code= status.HTTP_200_OK)
async def create(
    client: ClientCreate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ClientService(session).create(client, user.id)

