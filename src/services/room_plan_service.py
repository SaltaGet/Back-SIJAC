import logging
import uuid
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.room_appointment import RoomAppointment, StateAppointment
from src.models.room_plan import RoomPlan
from src.schemas.room.room_appointment import RoomAppointmentDTO
from src.schemas.room.room_plan import RoomPlanCreate, RoomPlanDTO, RoomPlanResponse
from sqlalchemy.orm import selectinload


class RoomPlanService:
  def __init__(self, session: AsyncSession):
    self.session = session

  async def create(self, room_plan_create: RoomPlanCreate):
    try:
      logging.info("Creando room plan")
      sttmt = select(RoomPlan).where(RoomPlan.tuition == room_plan_create.tuition)
      exist: RoomPlan | None = (await self.session.exec(sttmt)).first()

      if exist is not None:
        return JSONResponse(
          content={"detail": "Room plan ya existe"},
          status_code=status.HTTP_400_BAD_REQUEST
        )
      
      new_room_plan = RoomPlan(**room_plan_create.model_dump())
      self.session.add(new_room_plan)
      await self.session.commit()
      logging.info("Room plan creado!")
      return JSONResponse(
          content={
              "room_plan_id": new_room_plan.id
              },
          status_code=status.HTTP_201_CREATED
      )
    except Exception as e:
      logging.error("Error al intentar crear el room plan", e)
      await self.session.rollback()
      raise HTTPException(
          status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Error al intentar crear el room plan"
      )
    
  async def add_hours(self, room_plan_id: str, hours: int):
    try:
      logging.info("Agregando horas a room plan")
      sttmt = select(RoomPlan).where(RoomPlan.id == room_plan_id)
      room_plan: RoomPlan | None = (await self.session.exec(sttmt)).first()
      if room_plan is None:
        return JSONResponse(
          content={"detail": "Room plan no encontrado"},
          status_code=status.HTTP_404_NOT_FOUND
        )
      
      room_plan.total_hours += hours

      await self.session.commit()
      logging.info("Room plan actualizado!")
      return JSONResponse(
          content={
              "detail": "Room plan actualizado con exito"
              },
          status_code=status.HTTP_201_CREATED
      )
    except Exception as e:
      logging.error("Error al intentar actualizar el room plan", e)
      await self.session.rollback()
      raise HTTPException(
          status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Error al intentar actualizar el room plan"
      )
    
  async def assign_appointments(self, room_plan_id: str, appointments: list[str]):
    try:
      logging.info("Asignando citas a room plan")
      sttmt = select(RoomPlan).where(RoomPlan.id == room_plan_id)
      room_plan: RoomPlan | None = (await self.session.exec(sttmt)).first()
      if room_plan is None:
        return JSONResponse(
          content={"detail": "Room plan no encontrado"},
          status_code=status.HTTP_404_NOT_FOUND
        )

      sttmt = select(RoomAppointment).where(RoomAppointment.id.in_(appointments))
      appointment_create = (await self.session.exec(sttmt)).all()
      if len(appointment_create) != len(appointments):
        return JSONResponse(
          content={"detail": "Cita no encontrada"},
          status_code=status.HTTP_404_NOT_FOUND
        )

      new_uuid = uuid.UUID()

      for appointment in appointment_create: 
        appointment.first_name = room_plan.first_name
        appointment.last_name = room_plan.last_name
        appointment.email = room_plan.email
        appointment.cellphone = room_plan.cellphone
        appointment.tuition  = room_plan.tuition
        appointment.group_id = new_uuid
        appointment.room_plan_id = room_plan.id
        appointment.state = StateAppointment.ACCEPT

      await self.session.commit()
      logging.info("Room plan actualizado!")
      return JSONResponse(
          content={
              "detail": "turnos agregados con exito"
              },
          status_code=status.HTTP_201_CREATED
      )
    except Exception as e:
      logging.error("Error al intentar actualizar el room plan", e)
      await self.session.rollback()
      raise HTTPException(
          status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Error al intentar actualizar el room plan"
      )
    
  async def get(self, room_plan_id: str):
    try:
      logging.info("Obteniendo room plan")
      sttmt = select(RoomPlan).where(RoomPlan.id == room_plan_id).options(selectinload(RoomPlan.room_appointments))
      room_plan: RoomPlan | None = (await self.session.exec(sttmt)).first()
      
      if room_plan is None:
        return JSONResponse(
          content={"detail": "Room plan no encontrado"},
          status_code=status.HTTP_404_NOT_FOUND
        )

      room = RoomPlanResponse(
        **room_plan.model_dump(),
        appointmens = [RoomAppointmentDTO.validate(appointment) for appointment in room_plan.room_appointments]
      )

      return JSONResponse(
          content=room.model_dump(mode='json'),
          status_code=status.HTTP_200_OK
      )
    except Exception as e:
      logging.error(f"Error al obtener room plan: {e}")
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Error al intentar obtener el room plan"
      )
    
  async def get_all(self):
    try:
      logging.info("Obteniendo room plan")
      sttmt = select(RoomPlan)
      room_plan: list[RoomPlan] = (await self.session.exec(sttmt)).all()

      room_plans = [
        RoomPlanDTO.model_validate(room_plan).model_dump(mode='json')
        for room_plan in room_plans
      ]

      return JSONResponse(
          content=RoomPlan.model_validate(room_plan).model_dump(mode='json'),
          status_code=status.HTTP_200_OK
      )
    except Exception as e:
      logging.error(f"Error al obtener room plan: {e}")
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Error al intentar obtener el room plan"
      )
    
  async def delete(self, room_plan_id: str):
    try:
      logging.info("Eliminando room plan")
      sttmt = select(RoomPlan).where(RoomPlan.id == room_plan_id)
      room_plan: RoomPlan | None = (await self.session.exec(sttmt)).first()
      if room_plan is None:
        return JSONResponse(
          content={"detail": "Room plan no encontrado"},
          status_code=status.HTTP_404_NOT_FOUND
        )
      
      await self.session.delete(room_plan)
      await self.session.commit()

      logging.info("Room plan eliminado!")
      return JSONResponse(
          content={
              "detail": "Room plan eliminado con exito"
              },
          status_code=status.HTTP_200_OK
      )
    except Exception as e:
      logging.error(f"Error al editar room plan: {e}")
      await self.session.rollback()
      raise HTTPException(
          status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Error al intentar eliminar el room plan"
      )