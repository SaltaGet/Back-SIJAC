from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.appointment import StateAppointment
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.room.room_appointment import RoomAppointmentCreate, RoomAppointmentDTO, RoomAppointmentIds, RoomAppointmentResponse, RoomAppointmentResponseDTO
from src.services.appointment_service import AppointmentService
from src.services.auth_service import AuthService
from src.services.room_appointment_service import RoomAppointmentService


room_appointment_router = APIRouter(prefix='/room_appointment', tags=['RoomAppointment'])

auth = AuthService()

############################### GET ###############################

@room_appointment_router.get('/get_all/{room_availability_id}', response_model=list[RoomAppointmentDTO])
async def get_all(
    room_availability_id: str,
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    session: AsyncSession = Depends(db.get_session),
):
    today = date.today()
    
    if date_start and date_start < today:
        raise ValueError("date_start debe ser igual o mayor a hoy.")
    
    if date_end and date_end < today + timedelta(days=1):
        raise ValueError("date_end debe ser igual o mayor a mañana.")
    return await RoomAppointmentService(session).get_all(room_availability_id, date_start, date_end)

@room_appointment_router.get('/get_by_group/{group_id}', response_model=RoomAppointmentResponse)
async def get_by_group(
    group_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAppointmentService(session).get_by_group(group_id)

# @authorization(['admin','secretary'])
@room_appointment_router.get('/get/{id}', response_model=RoomAppointmentResponseDTO)
async def get(
    id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAppointmentService(session).get(id)

############################### PUT ###############################

@room_appointment_router.put('/update_state', status_code= status.HTTP_200_OK)
async def update(
    appointment_ids: RoomAppointmentIds,
    new_state: StateAppointment = Query(...),
    reason: str = Query(None),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    if new_state == StateAppointment.REJECT and not reason:
        raise ValueError("Debe indicar el motivo del rechazo")
    return await RoomAppointmentService(session).update_state(appointment_ids, new_state, reason)

@room_appointment_router.put('/create', status_code= status.HTTP_200_OK)
async def create(
    room_appointment_create: RoomAppointmentCreate,
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAppointmentService(session).create(room_appointment_create)

@room_appointment_router.put('/create_by_secretary', status_code= status.HTTP_200_OK)
async def create_by_secretary(
    appointment_create: RoomAppointmentCreate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomAppointmentService(session).create_by_secretary(appointment_create)

