from datetime import date, datetime, time, timedelta
import logging
from fastapi import HTTPException, status 
from src.models.appointment import Appointment, StateAppointment
from src.models.availability import Availability
from sqlmodel import asc, between, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from src.models.room_appointment import RoomAppointment
from src.models.room_availability import RoomAvailability
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_dto import AppointmentDto
from src.schemas.availability_schema.availability_dto import AvailabilityDto
from src.schemas.availability_schema.availability_response import AvailabilityResponseDto
from src.schemas.availability_schema.avaliability_update import AvailabilityUpdate
from src.schemas.room.room_appointment import RoomAppointmentDTO
from src.schemas.room.room_availability import RoomAvailabilityCreate, RoomAvailabilityDTO, RoomAvailabilityResponse, RoomAvailabilityUpdate
from src.services.email_service import EmailService


class RoomAvailabilityService:
  def __init__(self, session: AsyncSession):
      self.session = session

  async def create(self, room_available: RoomAvailabilityCreate):
    try:
        logging.info("Creando disponibilidad del room")

        sttmt_exist = select(RoomAvailability).where(
            RoomAvailability.date_all == room_available.date_all,
            RoomAvailability.room_id == room_available.room_id
        )
        available_exist: RoomAvailability | None = (await self.session.exec(sttmt_exist)).first()

        if available_exist is not None:
            return JSONResponse(
                content={"detail": "Ya existe la disponibilidad del día para room"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        new_available = RoomAvailability(**room_available.model_dump())
        self.session.add(new_available)
        await self.session.flush()

        async def create_appointments(start: time, end: time):
            slots: list[time] = await self.generate_time_slots(start, end)
            for slot in slots:
                new_appointment = RoomAppointment(
                    date_get=new_available.date_all,
                    start_time=slot,
                    end_time=(datetime.combine(datetime.today(), slot) + timedelta(minutes=60)).time(),
                    room_id=new_available.room_id,
                    room_availability_id=new_available.id
                )
                self.session.add(new_appointment)

        await create_appointments(new_available.start_time, new_available.end_time)

        await self.session.commit()
        logging.info("Disponibilidad del room creada!")

        return JSONResponse(
            content={"new_available": new_available.id},
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logging.error(f"Error al crear disponibilidad del room: {e}")
        await self.session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error al intentar crear la disponibilidad del room"
        )


  async def get_all(self, room_id: str, date_start: date = None, date_end: date = None):
      try:
          logging.info("Obteniendo Availabilities")
          if date_start is not None and date_end is not None:
              sttmt = select(RoomAvailability).where(
                  between(RoomAvailability.date_all, date_start, date_end)
              ).options(
                  joinedload(RoomAvailability.room_appointments)
              ).where(RoomAvailability.room_id == room_id)
          else: 
              sttmt = select(RoomAvailability
                          ).options(
                              joinedload(RoomAvailability.room_appointments)
                          ).where(RoomAvailability.room_id == room_id)
          
          availabilities: list[RoomAvailability] = (await self.session.exec(sttmt)).unique().all()

          list_availabilities: list[RoomAvailabilityDTO] = [
              RoomAvailabilityDTO(
                  id= avail.id,
                  date_all = avail.date_all,
                  start_time= avail.start_time,
                  end_time= avail.end_time,
                  disponibility = any(appointment.state == StateAppointment.NULL for appointment in avail.room_appointments),
              ).model_dump(mode='json')
              for avail in availabilities
          ]
          logging.info("Disponibilidades obtenidas")

          return JSONResponse(
              content= list_availabilities,
              status_code=status.HTTP_200_OK
          )
      except Exception as e:
          logging.error(f"Error al obtener disponibilidad: {e}")
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Error al intentar obtener la disponibilidad"
          )
      
  async def get(self, available_id: str, room_id: str):
      try:
          logging.info("Obteniendo disponibilidad")
          sttmt = select(RoomAvailability).options(
                  joinedload(RoomAvailability.room_appointments)
              ).where(
                  RoomAvailability.id == available_id,
              ).order_by(RoomAvailability.date_all.asc())
          
          exist_available: RoomAvailability | None = (await self.session.exec(sttmt)).first()

          if exist_available is None:
              return JSONResponse(
                  content={"detail": "Disponibilidad no encontrada"},
                  status_code=status.HTTP_404_NOT_FOUND
              )
          
          if exist_available.room_id != room_id:
              return JSONResponse(
                  content={"detail": "Disponibilidad erronea"},
                  status_code=status.HTTP_400_BAD_REQUEST
              )
          
          exist_available.room_appointments.sort(key=lambda appt: appt.start_time)
          
          appointments_data = [
            RoomAppointmentDTO(
                id= appointment.id,
                group_id= appointment.group_id,
                date_get= appointment.date_get, 
                start_time= appointment.start_time, 
                state= appointment.state  
              ).model_dump(mode='json') 
              for appointment in exist_available.room_appointments
            ]
          
          logging.info("Disponibilidad del room obtenida")

          return JSONResponse(
              content=RoomAvailabilityResponse.model_validate({
                  **exist_available.model_dump(),
                  "appointments": appointments_data
              }).model_dump(mode='json'),
              status_code=status.HTTP_200_OK
          )
      except Exception as e:
          logging.error(f"Error al obtener disponibilidad del room: {e}")
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Error al intentar obtener la disponibilidad"
          )
      
  async def update(self, available_id: str, available_update: RoomAvailabilityUpdate):
      try:
          logging.info("Actualizando disponibilidad")
          sttmt = select(RoomAvailability).options(
              joinedload(RoomAvailability.room_appointments)
          ).where(RoomAvailability.id == available_id)
          available: RoomAvailability | None = (await self.session.exec(sttmt)).first()

          if available is None:
              return JSONResponse(
                  content={"detail": "Disponibilidad no encontrada"},
                  status_code=status.HTTP_404_NOT_FOUND
              )

          if available.date_all == date.today():
              return JSONResponse(
                  content={"detail": "No se puede modificar la fecha de hoy"},
                  status_code=status.HTTP_400_BAD_REQUEST
              )

          available.room_appointments.sort(key=lambda appt: appt.start_time)

          active_appts = [
              appt for appt in available.room_appointments
              if appt.state in [StateAppointment.PENDING, StateAppointment.ACCEPT, StateAppointment.RESERVED]
          ]

          if not active_appts:
              available.start_time = available_update.start_time
              available.end_time = available_update.end_time

              for appointment in available.room_appointments:
                  await self.session.delete(appointment)

              slots: list[time] = []
              slots += await self.generate_time_slots(available_update.start_time, available_update.end_time)

              for slot in slots:
                  new_appointment = RoomAppointment(
                      date_get=available.date_all,
                      start_time=slot,
                      end_time=(datetime.combine(datetime.today(), slot) + timedelta(minutes=60)).time(),
                      room_availability_id=available.id,
                      room_id=available.room_id
                  )
                  self.session.add(new_appointment)

              await self.session.commit()

              logging.info("Disponibilidad actualizada")
              return JSONResponse(
                  content={'detail': 'Disponibilidad editada con éxito!'},
                  status_code=status.HTTP_200_OK
              )

          end_time_naive = available_update.end_time.replace(tzinfo=None)
          dt = datetime.combine(datetime.today(), end_time_naive)
          dt_minus_1h = dt - timedelta(hours=1)
          new_time = dt_minus_1h.time()
          updated_ranges = [
                (
                    available_update.start_time.replace(tzinfo=None) if available_update.start_time else None,
                    new_time
                )
          ]

          for appt in active_appts:
              if not any(start <= appt.start_time <= end for start, end in updated_ranges):
                  return JSONResponse(
                      content={"detail": f"No se puede modificar el horario. Existen turnos activos fuera del nuevo rango: {appt.start_time.strftime('%H:%M')}"},
                      status_code=status.HTTP_400_BAD_REQUEST
                  )

          appointment_save = []
          for appoint in available.room_appointments:
              if appoint.state in [StateAppointment.NULL, StateAppointment.CANCEL, StateAppointment.REJECT]:
                  if appoint.state == StateAppointment.RESERVED:
                      reason = "Se ha modificado la disponibilidad del día, por favor contactarte nuevamente con SIJAC, o enviar un turno nuevo desde nuestra web"
                  await self.session.delete(appoint)
              else:
                  appointment_save.append(appoint.start_time)

          await self.session.flush()

          slots: list[time] = []
          slots += await self.generate_time_slots(available_update.start_time, available_update.end_time)

          for slot in slots:
              if slot not in appointment_save:
                  new_appointment = RoomAppointment(
                      date_get=available.date_all,
                      start_time=slot,
                      end_time=(datetime.combine(datetime.today(), slot) + timedelta(minutes=60)).time(),
                      room_availability_id=available.id,
                      room_id=available.room_id
                  )
                  self.session.add(new_appointment)

          available.start_time = available_update.start_time
          available.end_time = available_update.end_time

          await self.session.commit()

          logging.info("Disponibilidad actualizada")
          return JSONResponse(
              content={'detail': 'Disponibilidad editada con éxito!'},
              status_code=status.HTTP_200_OK
          )

      except Exception as e:
          logging.error(f"Error al editar disponibilidad: {e}")
          await self.session.rollback()
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Error al intentar editar la disponibilidad"
          )

      
  async def delete(self, available_id: str):
      try:
          logging.info("Eliminando disponibilidad")
          sttmt = select(RoomAvailability).options(
              joinedload(RoomAvailability.room_appointments)
          ).where(RoomAvailability.id == available_id)
          available: RoomAvailability | None = (await self.session.exec(sttmt)).first()

          available: RoomAvailability | None = await self.session.get(RoomAvailability, available_id)
          
          if available is None:
              return JSONResponse(
                  content={"detail": "Disponibilidad no encontrada"},
                  status_code=status.HTTP_404_NOT_FOUND
              )
          
          for appointment in available.room_appointments:
              if appointment.state == StateAppointment.PENDING or appointment.state == StateAppointment.ACCEPT:
                  reason = "Se ha eliminado la disponibilidad del día, por favor contactarte nuevamente con SIJAC, o enviar un nuevamente desde nuestra web"
                  await EmailService().send_email_client(StateAppointment.REJECT, appointment, reason)
              await self.session.delete(appointment)
          
          await self.session.delete(available)

          await self.session.commit()

          logging.info("Disponibilidad del room eliminada")

          JSONResponse(
              content= {"detail": "Disponibilidad del room eliminada con exito!"},
              status_code=status.HTTP_200_OK
          )
      except Exception as e:
          logging.error(f"Error al eliminar Disponibilidad del room: {e}")
          await self.session.rollback()
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Error al intentar eliminar disponibilidad del room"
          )
      
  async def generate_time_slots(self, start_time: time, end_time: time, interval_minutes: int = 60):
      slots = []
      current_time = datetime.combine(datetime.today(), start_time)
      end_datetime = datetime.combine(datetime.today(), end_time)

      while current_time+timedelta(minutes=interval_minutes) <= end_datetime:
          slots.append(current_time.time())  
          current_time += timedelta(minutes=interval_minutes)  

      return slots