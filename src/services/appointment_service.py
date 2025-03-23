from datetime import date, datetime, timedelta
import logging
import asyncio
from fastapi import HTTPException, status
from src.config.timezone import get_timezone
from src.models.appointment import Appointment, StateAppointment
from sqlmodel import between, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.appointment_schema.appointment_response import AppointmentResponse
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
import copy


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
            exist_appointment.state = StateAppointment.RESERVED
            token, expire = await AuthService().create_token_appointment(exist_appointment.id, exist_appointment.user_id)
            exist_appointment.token = token


            await EmailService().send_email_client(StateAppointment.RESERVED, exist_appointment, None, token)
            asyncio.create_task(self.delete_reserv(appointment_create.id, expire))

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
        
    async def update_state(self, appointment_id: str, user_id: str, new_state: StateAppointment, reason: str = None):
        try:
            logging.info("Obteniendo turno")
            sttmt = select(Appointment).where(Appointment.id == appointment_id).where(Appointment.user_id == user_id)
            appointment: Appointment | None = (await self.session.exec(sttmt)).first()

            if appointment is None:
                return JSONResponse(
                    content={"detail": "Turno no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # if datetime.combine(apointment.date_get, apointment.start_time) >= datetime.now(timezone.utc) + timedelta(hours=2):
            if datetime.combine(appointment.date_get, appointment.start_time) <= get_timezone() + timedelta(hours=2):
                return JSONResponse(
                    content={"detail": "No es posible cambiar el estado de un turno antes de 2 hrs de su inicio"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            appointment_copy = copy.copy(appointment)

            if new_state not in [StateAppointment.ACCEPT, StateAppointment.REJECT]:
                appointment.state = StateAppointment.NULL
                appointment.full_name = None
                appointment.email = None
                appointment.cellphone = None
                appointment.reason = None
                appointment.token = None
            else:
                appointment.state = new_state

            await self.session.commit()

            await EmailService().send_email_client(new_state, appointment_copy, reason)

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
        
    async def confirm(self, token: str):
        try:
            logging.info("Confirmando turno")
            data = await AuthService().decode_token(token)

            if data is False:
                return JSONResponse(
                    content={"detail": "Token expirado, realice una reserva nuevamente"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            sttmt = select(Appointment).where(Appointment.id == data['appointment_id']
                ).where(Appointment.user_id == data['user_id']
                ).where(Appointment.token == token)
            
            appointment: Appointment | None = (await self.session.exec(sttmt)).first()

            if appointment is None:
                return JSONResponse(
                    content={"detail": "Turno no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            user: User = await self.session.get(User, appointment.user_id)
            
            appointment.state = StateAppointment.PENDING

            await self.session.commit()

            # await EmailService().send_email_lawyer(appointment, user.email)
            await EmailService().send_email_lawyer(appointment, 'danielmchachagua@gmail.com')

            logging.info("Turno confirmado")
            return JSONResponse(
                content= {'detail': 'Turno confirmado con exito!'},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al confirmar turno: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar confirmar el turno"
            )
        
    async def delete_reserv(self, appointment_id: str, execution_time: datetime):
        wait_seconds = (execution_time - datetime.now()).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        sttmt = select(Appointment).where(Appointment.id == appointment_id
                                    ).where(Appointment.state == StateAppointment.RESERVED
                                    ).where(Appointment.token != None)
        appointment: Appointment | None = (await self.session.exec(sttmt)).first()

        if appointment:
            appointment.state = StateAppointment.NULL
            appointment.full_name = None
            appointment.email = None
            appointment.cellphone = None
            appointment.reason = None
            appointment.token = None 
            await self.session.commit()
            logging.info(f"Turno {appointment_id} ha sido cancelado automáticamente.")
        else:
            logging.error(f"Error al cancelar Turno {appointment_id}")