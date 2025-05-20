from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.appointment import StateAppointment
from src.models.case import StateCase
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.case.case_create import CaseCreate
from src.schemas.case.case_update import CaseUpdate
from src.services.appointment_service import AppointmentService
from src.services.audit_service import AuditService
from src.services.auth_service import AuthService
from src.services.case_service import CaseService


audit_router = APIRouter(prefix='/audit', tags=['Audit'])

auth = AuthService()

############################### GET ###############################

@authorization(['admin'])
@audit_router.get('/get_all')
async def get_all(
  page: int = Query(1, alias="page", ge=1),
  per_page: int = Query(9, alias="per_page", ge=1, le=50),
  user: User = Depends(auth.get_current_user),
  session: AsyncSession = Depends(db.get_session),
):
  return await AuditService(session).get_all(page, per_page)

@authorization(['admin'])
@audit_router.get('/get/{audit_id}')
async def get(
    audit_id: str,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
  return await AuditService(session).get(audit_id)