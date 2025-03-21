from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database.db import db
from src.models.user_model import User
from src.schemas.availability_schema.availability_create import AvailabilityCreate
from src.schemas.availability_schema.avaliability_update import AvailabilityUpdate
from src.services.auth_service import AuthService
from src.services.availability_service import AvailabilityService

availability_router = APIRouter(prefix='/availability', tags=['Availability'])

auth = AuthService()

############################### POST ###############################

@availability_router.post('/create', status_code= status.HTTP_201_CREATED)
async def create(
    available: AvailabilityCreate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await AvailabilityService(session).create(available, user)

############################### GET ###############################

@availability_router.get('/get_all/{user_id}')
async def get_all(
    user_id: str,
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    session: AsyncSession = Depends(db.get_session),
):
    today = date.today()
    
    if date_start and date_start < today:
        raise ValueError("date_start debe ser igual o mayor a hoy.")
    
    if date_end and date_end < today + timedelta(days=1):
        raise ValueError("date_end debe ser igual o mayor a mañana.")
    return await AvailabilityService(session).get_all(user_id,date_start, date_end)

@availability_router.get('/get/{available_id}')
async def get(
    available_id: str,
    user_id: str = Query(...),
    session: AsyncSession = Depends(db.get_session),
):
    return await AvailabilityService(session).get(available_id, user_id)

############################### PUT ###############################

@availability_router.put('/update/{available_id}', status_code= status.HTTP_200_OK)
async def update(
    available_id: str,
    available_update: AvailabilityUpdate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await AvailabilityService(session).update(available_id, available_update, user.id)

############################### DELETE ###############################

@availability_router.delete('/delete/{available_id}')
async def delete(
    available_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await AvailabilityService(session).delete(available_id, user.id)

