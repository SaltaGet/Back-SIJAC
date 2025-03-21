from datetime import date, datetime, timedelta
import logging
from fastapi import HTTPException, status
from src.config.timezone import get_timezone
from src.models.appointment import Appointment, StateAppointment
from sqlmodel import between, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.appointment_schema.appointment_response import AppointmentResponse


class AppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, appointment_create: AppointmentCreate):
        try:
            logging.info("Creando turno")
            exist_appointment: Appointment | None = await self.session.get(Appointment, appointment_create.id)

            if exist_appointment is None:
                return JSONResponse(
                    content={
                        "detail": "Turno no encontrado"
                        },
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            if exist_appointment.state != StateAppointment.NULL:
                return JSONResponse(
                    content={
                        "detail": "El turno ya fue asignado"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if exist_appointment.date_get <= date.today():
                return JSONResponse(
                    content={
                        "detail": "La fecha debe ser posterior al día de hoy"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            exist_appointment.full_name = appointment_create.full_name
            exist_appointment.email = appointment_create.email
            exist_appointment.cellphone = appointment_create.cellphone
            exist_appointment.reason = appointment_create.reason
            exist_appointment.state = StateAppointment.PENDING

            await self.session.commit()

            logging.info("Turno asignado")

            return JSONResponse(
                    content={
                        "detail": "turno asignado con exito!"
                        },
                    status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al crear turno: {e}")
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear el turno")

    async def get_all(self, user_id: str, date_start: date = None, date_end: date = None):
        try:
            logging.info("Obteniendo Turnos")
            if date_start is not None and date_end is not None:
                sttmt = select(Appointment).where(
                    between(Appointment.date_get, date_start, date_end)
                ).where(Appointment.user_id == user_id)
            else: 
                sttmt = select(Appointment).where(Appointment.user_id == user_id)
           
            appointments: list[Appointment] = (await self.session.exec(sttmt)).all()

            list_appointments: list[AppointmentResponse] = [
                AppointmentResponse.model_validate(appoint).model_dump(mode='json')
                for appoint in appointments
            ]
            logging.info("Disponibilidades obtenidas")

            return JSONResponse(
                content= list_appointments,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener turnos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el turno"
            )
        
    async def get(self, appointment_id: str, user_id: str):
        try:
            logging.info("Obteniendo turno")
            sttmt = select(Appointment).where(Appointment.id == appointment_id).where(Appointment.user_id == user_id)
            apointment: Appointment | None = (await self.session.exec(sttmt)).first()

            if apointment is None:
                return JSONResponse(
                    content={"detail": "Turno no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return JSONResponse(
                content=AppointmentResponse.model_validate(apointment).model_dump(mode='json'),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener turno: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el turno"
            )
        
    async def update_state(self, appointment_id: str, user_id: str, new_state: StateAppointment):
        try:
            logging.info("Obteniendo turno")
            sttmt = select(Appointment).where(Appointment.id == appointment_id).where(Appointment.user_id == user_id)
            apointment: Appointment | None = (await self.session.exec(sttmt)).first()

            if apointment is None:
                return JSONResponse(
                    content={"detail": "Turno no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # if datetime.combine(apointment.date_get, apointment.start_time) >= datetime.now(timezone.utc) + timedelta(hours=2):
            if datetime.combine(apointment.date_get, apointment.start_time) <= get_timezone() + timedelta(hours=2):
                return JSONResponse(
                    content={"detail": "No es posible cambiar el estado de un turno antes de 2 hrs de su inicio"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if new_state not in [StateAppointment.ACCEPT, StateAppointment.REJECT]:
                apointment.state = StateAppointment.NULL
                apointment.full_name = None
                apointment.email = None
                apointment.cellphone = None
                apointment.reason = None
            else:
                apointment.state = new_state

            await self.session.commit()

            logging.info("Turno actualizado")
            return JSONResponse(
                content= {'detail': 'Turno editado con exito!'},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al editar Turno: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el Turno"
            )
        
