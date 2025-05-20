from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database.db import db
from src.models.appointment import StateAppointment
from src.models.case import StateCase
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.case.case_create import CaseCreate
from src.schemas.case.case_update import CaseUpdate
from src.services.appointment_service import AppointmentService
from src.services.auth_service import AuthService
from src.services.case_service import CaseService


case_router = APIRouter(prefix='/case', tags=['Case'])

auth = AuthService()

############################### GET ###############################

@case_router.get('/get_all')
async def get_all(
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
  return await CaseService(session).get_all(user.id)

@case_router.get('/get/{case_id}')
async def get(
    case_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).get(case_id, user.id)

@case_router.get('/get_by_client/{client_id}')
async def get_by_client(
    client_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).get_by_client(client_id, user.id)

@case_router.get('/get_by_state/')
async def get_by_state(
    state: StateCase = Query(...),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
  return await CaseService(session).get_by_state(state, user.id)

############################### PUT ###############################

@case_router.put('/update/{case_id}', status_code= status.HTTP_200_OK)
async def update(
    case_id: str,
    case_update: CaseUpdate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).update(case_id, case_update, user.id)

@case_router.put('/update_state/{case_id}', status_code= status.HTTP_200_OK)
async def update_state(
    case_id: str,
    state: StateCase = Query(...),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).update_state(case_id, state, user.id)

@case_router.put('/share_case/{case_id}', status_code= status.HTTP_200_OK)
async def share_case(
    case_id: str,
    user_shared: str = Query(...),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).share_case(case_id, user_shared, user.id)

@case_router.put('/unshare_case/{case_id}', status_code= status.HTTP_200_OK)
async def unshare_case(
    case_id: str,
    user_unshared: str = Query(...),
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).unshare_case(case_id, user_unshared, user.id)

############################### POST ###############################

@case_router.post('/create', status_code= status.HTTP_200_OK)
async def create(
    case: CaseCreate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).create(case, user.id)

############################### DELETE ###############################

@case_router.delete('/delete/{case_id}', status_code= status.HTTP_200_OK)
async def delete(
    case_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await CaseService(session).create(case_id, user.id)



