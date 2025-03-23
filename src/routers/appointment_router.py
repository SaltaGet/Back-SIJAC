from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database.db import db
from src.models.appointment import StateAppointment
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.services.appointment_service import AppointmentService
from src.services.auth_service import AuthService


appointment_router = APIRouter(prefix='/appointment', tags=['Appointment'])

auth = AuthService()

############################### GET ###############################

@appointment_router.get('/get_all/{user_id}')
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
    return await AppointmentService(session).get_all(user_id, date_start, date_end)

@appointment_router.get('/get/{appointment_id}')
async def get(
    appointment_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await AppointmentService(session).get(appointment_id, user.id)

############################### PUT ###############################

@appointment_router.put('/update_state/{appointment_id}', status_code= status.HTTP_200_OK)
async def update(
    appointment_id: str,
    new_state: StateAppointment = Query(...),
    reason: str = Query(None),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    if new_state == StateAppointment.REJECT and not reason:
        raise ValueError("Debe indicar el motivo del rechazo")
    return await AppointmentService(session).update_state(appointment_id, user.id, new_state, reason)

@appointment_router.put('/create', status_code= status.HTTP_200_OK)
async def create(
    appointment_create: AppointmentCreate,
    session: AsyncSession = Depends(db.get_session),
):
    return await AppointmentService(session).create(appointment_create)

############################### POST ###############################

@appointment_router.post('/confirm', status_code= status.HTTP_200_OK)
async def confirm(
    token: str = Query(...),
    session: AsyncSession = Depends(db.get_session),
):
    return await AppointmentService(session).confirm(token)