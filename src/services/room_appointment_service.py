from collections import defaultdict
from datetime import date, datetime, timedelta
import logging
from fastapi import HTTPException, status
from src.config.timezone import get_timezone
from src.models.appointment import Appointment, StateAppointment
from sqlmodel import between, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.models.room_appointment import RoomAppointment
from src.models.user_model import User
from src.schemas.room.room_appointment import RoomAppointmentCreate, RoomAppointmentDTO, RoomAppointmentIds, RoomAppointmentResponse, RoomAppointmentResponseDTO
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
import copy
from uuid import uuid4


class RoomAppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, appointment_create: RoomAppointmentCreate):
        try:
            logging.info("Creando turno")         
            sttmt = (
                select(RoomAppointment)
                .where(RoomAppointment.id.in_(appointment_create.appointment_ids))
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
            
            today = date.today()

            if len(result) != len(appointment_create.appointment_ids):
                return JSONResponse(
                    content={
                        "detail": "Hay turno que no fueron encontrados o no estan disponibles"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            for appointment in result:    
                if appointment.date_get <= today:
                    return JSONResponse(
                        content={
                            "detail": "La fecha debe ser posterior al día de hoy"
                            },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )        
                if appointment.state != StateAppointment.NULL:
                    return JSONResponse(
                        content={
                            "detail": f"El turno de {appointment.start_time} a {appointment.end_time} ya fue asignado"
                            },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            
            uuid = str(uuid4())
            
            for exist_appointment in result:
                exist_appointment.group_id = uuid
                exist_appointment.first_name = appointment_create.first_name
                exist_appointment.last_name = appointment_create.last_name
                exist_appointment.email = appointment_create.email
                exist_appointment.cellphone = appointment_create.cellphone
                exist_appointment.tuition = appointment_create.tuition
                exist_appointment.state = StateAppointment.RESERVED

            # await EmailService().send_email_client(StateAppointment.RESERVED, result[0], None, "")

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
            sttmt = (
                select(RoomAppointment)
                .where(RoomAppointment.id.in_(appointment_create.appointment_ids))
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
            
            today = date.today()

            if len(result) != len(appointment_create.appointment_ids):
                return JSONResponse(
                    content={
                        "detail": "Hay turno que no fueron encontrados o no estan disponibles"
                        },
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            uuid = str(uuid4())

            for appointment in result:    
                if appointment.date_get <= today:
                    return JSONResponse(
                        content={
                            "detail": "La fecha debe ser posterior al día de hoy"
                            },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )        
                if appointment.state != StateAppointment.NULL:
                    return JSONResponse(
                        content={
                            "detail": f"El turno de {appointment.start_time} a {appointment.end_time} ya fue asignado"
                            },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                appointment.group_id = uuid
                appointment.first_name = appointment_create.first_name
                appointment.last_name = appointment_create.last_name
                appointment.email = appointment_create.email
                appointment.cellphone = appointment_create.cellphone
                appointment.tuition = appointment_create.tuition
                appointment.state = StateAppointment.RESERVED

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
            appointments.sort(key=lambda x: x.start_time)

            logging.info("Disponibilidades obtenidas")

            return JSONResponse(
                content= [RoomAppointmentDTO.model_validate(appt).model_dump(mode='json') for appt in appointments], #[appt.model_dump(mode='json') for appt in appointments],
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener turnos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el turno"
            )
    
    async def get(self, id: str):
        try:
            logging.info("Obteniendo turno")
            sttmt = (
                select(RoomAppointment)
                .where(RoomAppointment.id == id)
            )
           
            appointment: RoomAppointment | None = (await self.session.exec(sttmt)).first()

            if appointment is None:
                return JSONResponse(
                    content={"detail": "Turno no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return JSONResponse(
                content=RoomAppointmentResponseDTO.model_validate(appointment).model_dump(mode='json'),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener turno: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el turno"
            )
        
    async def get_by_group(self, group_id: str):
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
                appt_list.sort(key=lambda x: x.start_time)
                first_appt = appt_list[0]
                last_appt = appt_list[-1]
                responses.append(RoomAppointmentResponse(
                    group_id=group_id,
                    date_get=first_appt.date_get,
                    start_time=first_appt.start_time,
                    end_time=last_appt.end_time,
                    first_name=first_appt.first_name,
                    last_name=first_appt.last_name,
                    email=first_appt.email,
                    cellphone=first_appt.cellphone,
                    tuition=first_appt.tuition,
                    state=first_appt.state,
                    room_availability_id=first_appt.room_availability_id,
                    appointments=[appt.model_dump(mode='json') for appt in appt_list]
                ).model_dump(mode='json'))
            
            return JSONResponse(
                content=responses[0],
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener turno: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el turno"
            )
        
    async def update_state(self, appointment_ids: RoomAppointmentIds, new_state: StateAppointment, reason: str = None):
        try:
            logging.info("Obteniendo turno")
            sttmt = select(RoomAppointment).where(RoomAppointment.id.in_(appointment_ids.appointment_ids))
            appointments: list[RoomAppointment] = (await self.session.exec(sttmt)).all()

            if len(appointments) == 0:
                return JSONResponse(
                    content={"detail": "Turno nos encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            for appointment in appointments:
                if datetime.combine(appointment.date_get, appointment.start_time) <= get_timezone() + timedelta(hours=2):
                    return JSONResponse(
                        content={"detail": "No es posible cambiar el estado de un turno antes de 2 hrs de su inicio"},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                if new_state not in [StateAppointment.ACCEPT, StateAppointment.REJECT]:
                    appointment.state = StateAppointment.NULL
                    appointment.first_name = None
                    appointment.last_name = None
                    appointment.email = None
                    appointment.cellphone = None
                    appointment.group_id = None
                    appointment.tuition = None
                else:
                    appointment.state = new_state

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
        
        