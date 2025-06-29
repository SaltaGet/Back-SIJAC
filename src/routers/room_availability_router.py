from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import User
from src.schemas.availability_schema.availability_create import AvailabilityCreate
from src.schemas.availability_schema.avaliability_update import AvailabilityUpdate
from src.schemas.room.room_appointment import RoomAppointmentDTO
from src.schemas.room.room_availability import RoomAvailabilityCreate, RoomAvailabilityDTO, RoomAvailabilityResponse, RoomAvailabilityUpdate
from src.services.auth_service import AuthService
from src.services.availability_service import AvailabilityService
from src.services.room_availability_service import RoomAvailabilityService

room_availability_router = APIRouter(prefix='/room_availability', tags=['RoomAvailability'])

auth = AuthService()

############################### POST ###############################
# @authorization(['admin'])
@room_availability_router.post('/create', status_code= status.HTTP_201_CREATED)
async def create(
    availables: list[RoomAvailabilityCreate],
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAvailabilityService(session).create(availables)

############################### GET ###############################
@room_availability_router.get('/get_all/{room_id}', response_model=list[RoomAvailabilityDTO])
async def get_all(
    room_id: str,
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    session: AsyncSession = Depends(db.get_session),
):
    today = date.today()
    
    if date_start and date_start < today:
        raise ValueError("date_start debe ser igual o mayor a hoy.")
    
    if date_end and date_end < today + timedelta(days=1):
        raise ValueError("date_end debe ser igual o mayor a mañana.")
    return await RoomAvailabilityService(session).get_all(room_id ,date_start, date_end)

@room_availability_router.get('/get/{available_id}', response_model=list[RoomAvailabilityResponse])
async def get(
    available_id: str,
    room_id: str = Query(...),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAvailabilityService(session).get(available_id, room_id)

############################### PUT ###############################
# @authorization(['admin'])
@room_availability_router.put('/update/{available_id}', status_code= status.HTTP_200_OK)
async def update(
    available_id: str,
    available_update: RoomAvailabilityUpdate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAvailabilityService(session).update(available_id, available_update)

############################### DELETE ###############################
# @authorization(['admin'])
@room_availability_router.delete('/delete/{available_id}')
async def delete(
    available_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAvailabilityService(session).delete(available_id)

