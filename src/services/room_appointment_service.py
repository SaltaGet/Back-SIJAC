from collections import defaultdict
from datetime import date, datetime, timedelta
import logging
import asyncio
from fastapi import HTTPException, status
from src.config.timezone import get_timezone
from src.models.appointment import Appointment, StateAppointment
from sqlmodel import between, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.models.room_appointment import RoomAppointment
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.appointment_schema.appointment_response import AppointmentResponse
from src.schemas.room.room_appointment import RoomAppointmentCreate, RoomAppointmentDTO, RoomAppointmentResponse
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
import copy


class RoomAppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, appointment_create: RoomAppointmentCreate):
        try:
            logging.info("Creando turno")
            if appointment_create.date_get <= date.today():
                return JSONResponse(
                    content={
                        "detail": "La fecha debe ser posterior al día de hoy"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            sttmt = (
                select(RoomAppointment)
                .where(RoomAppointment.date_get == appointment_create.date_get)
                .where(between(RoomAppointment.start_time, appointment_create.first_time, appointment_create.last_time))
                .where(RoomAppointment.room_availability_id == appointment_create.room_availability_id)
            )
            result = (await self.session.exec(sttmt)).all()

            if len(result) == 0:
                return JSONResponse(
                    content={
                        "detail": "No hay turnos disponibles"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            for appointment in result:            
                if appointment.state != StateAppointment.NULL:
                    return JSONResponse(
                        content={
                            "detail": f"El turno de {appointment.start_time} a {appointment.end_time} ya fue asignado"
                            },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            
            uuid = str(uuid.uuid4())
            
            for exist_appointment in result:
                exist_appointment.group_id = uuid
                exist_appointment.first_name = appointment_create.first_name
                exist_appointment.last_name = appointment_create.last_name
                exist_appointment.email = appointment_create.email
                exist_appointment.cellphone = appointment_create.cellphone
                exist_appointment.tuition = appointment_create.tuition
                exist_appointment.state = StateAppointment.RESERVED

            await EmailService().send_email_client(StateAppointment.RESERVED, result[0], None, "")

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
    
    async def create_by_secretary(self, appointment_create: RoomAppointmentCreate):
        try:
            logging.info("Creando turno")
            if appointment_create.date_get <= date.today():
                return JSONResponse(
                    content={
                        "detail": "La fecha debe ser posterior al día de hoy"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            sttmt = (
                select(RoomAppointment)
                .where(RoomAppointment.date_get == appointment_create.date_get)
                .where(between(RoomAppointment.start_time, appointment_create.first_time, appointment_create.last_time))
                .where(RoomAppointment.room_availability_id == appointment_create.room_availability_id)
            )
            result = (await self.session.exec(sttmt)).all()

            for appointment in result:            
                if appointment.state != StateAppointment.NULL:
                    return JSONResponse(
                        content={
                            "detail": f"El turno de {appointment.start_time} a {appointment.end_time} ya fue asignado"
                            },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            
            
            for exist_appointment in result:
                exist_appointment.first_name = appointment_create.first_name
                exist_appointment.last_name = appointment_create.last_name
                exist_appointment.email = appointment_create.email
                exist_appointment.cellphone = appointment_create.cellphone
                exist_appointment.tuition = appointment_create.tuition
                exist_appointment.state = StateAppointment.RESERVED

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

    async def get_all(self, room_availability_id: str, date_start: date = None, date_end: date = None):
        try:
            logging.info("Obteniendo Turnos")
            if date_start is not None and date_end is not None:
                sttmt = (
                  select(RoomAppointment)
                  .where(between(RoomAppointment.date_get, date_start, date_end))
                  .where(RoomAppointment.room_availability_id == room_availability_id)
                  .order_by(RoomAppointment.group_id, RoomAppointment.start_time)
                )
            else: 
                sttmt = (
                    select(RoomAppointment)
                    .where(RoomAppointment.room_availability_id == room_availability_id)
                    .order_by(RoomAppointment.group_id, RoomAppointment.start_time)
                )
           
            appointments: list[RoomAppointment] = (await self.session.exec(sttmt)).all()

            grouped = defaultdict(list)
            for appt in appointments:
                grouped[appt.group_id].append(appt)

            responses = []
            for group_id, appt_list in grouped.items():
                # appt_list.sort(key=lambda x: x.start_time)
                first_appt = appt_list[0]
                last_appt = appt_list[-1]
                responses.append(RoomAppointmentDTO(
                    group_id=group_id,
                    date_get=first_appt.date_get,
                    first_time=first_appt.start_time,
                    last_time=last_appt.start_time,
                ))
            logging.info("Disponibilidades obtenidas")

            return JSONResponse(
                content= [appt.model_dump(mode='json') for appt in responses],
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener turnos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el turno"
            )
        
    async def get(self, group_id: str):
        try:
            logging.info("Obteniendo turno")
            sttmt = (
                select(RoomAppointment)
                .where(RoomAppointment.group_id == group_id)
                .order_by(RoomAppointment.group_id, RoomAppointment.start_time)
            )
           
            appointments: list[RoomAppointment] = (await self.session.exec(sttmt)).all()

            if len(appointments) == 0:
                return JSONResponse(
                    content={"detail": "Turno no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            grouped = defaultdict(list)
            for appt in appointments:
                grouped[appt.group_id].append(appt)

            responses = []
            for group_id, appt_list in grouped.items():
                # appt_list.sort(key=lambda x: x.start_time)
                first_appt = appt_list[0]
                last_appt = appt_list[-1]
                responses.append(RoomAppointmentResponse(
                    group_id=group_id,
                    date_get=first_appt.date_get,
                    first_time=first_appt.start_time,
                    last_time=last_appt.start_time,
                    first_name=first_appt.first_name,
                    last_name=first_appt.last_name,
                    email=first_appt.email,
                    cellphone=first_appt.cellphone,
                    tuition=first_appt.tuition,
                    state=first_appt.state
                ))
            
            return JSONResponse(
                content=responses[0].model_dump(mode='json'),
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

            await EmailService().send_email_lawyer(appointment, user.email)
            # await EmailService().send_email_lawyer(appointment, 'danielmchachagua@gmail.com')

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
        