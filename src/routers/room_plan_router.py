from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import User
from src.schemas.room.room_plan import RoomPlanAddAppointmentIds, RoomPlanCreate, RoomPlanDTO, RoomPlanResponse, RoomPlanUpdateHours
from src.services.auth_service import AuthService
from src.services.room_plan_service import RoomPlanService


room_plan_router = APIRouter(prefix='/room_plan', tags=['RoomPlan'])

auth = AuthService()

############################### GET ###############################

@room_plan_router.get('/get_all', response_model=list[RoomPlanDTO])
async def get_all(
    # user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomPlanService(session).get_all()

# @authorization(['admin','secretary'])
@room_plan_router.get('/get/{room_plan_id}', response_model=RoomPlanResponse)
async def get(
    room_plan_id: str,
    # user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomPlanService(session).get(room_plan_id)

############################### PUT ###############################

@room_plan_router.put('/add_hours/{room_plan_id}', status_code= status.HTTP_200_OK)
async def update(
    room_plan_id: str,
    hours: RoomPlanUpdateHours,
    # user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomPlanService(session).add_hours(room_plan_id, hours.hours)

@room_plan_router.put('/assign_appointments/{room_plan_id}', status_code= status.HTTP_200_OK)
async def create(
    room_plan_id: str,
    appointment_ids: RoomPlanAddAppointmentIds,
    # user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomPlanService(session).assign_appointments(room_plan_id, appointment_ids.appointment_ids)

############################### POST ###############################
@room_plan_router.post('/create', status_code= status.HTTP_201_CREATED)
async def create(
    room_plan_create: RoomPlanCreate,
    # user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomPlanService(session).create(room_plan_create)

############################### DELETE ###############################

@room_plan_router.delete('/delete/{room_plan_id}', status_code= status.HTTP_200_OK)
async def delete(
    room_plan_id: str,
    # user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await RoomPlanService(session).delete(room_plan_id)