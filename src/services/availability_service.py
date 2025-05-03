from datetime import date, datetime, time, timedelta
import logging
from fastapi import HTTPException, status 
from src.models.appointment import Appointment, StateAppointment
from src.models.availability import Availability
from sqlmodel import asc, between, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_dto import AppointmentDto
from src.schemas.availability_schema.availability_create import AvailabilityCreate
from src.schemas.availability_schema.availability_dto import AvailabilityDto
from src.schemas.availability_schema.availability_response import AvailabilityResponseDto
from src.schemas.availability_schema.avaliability_update import AvailabilityUpdate
from src.services.email_service import EmailService


class AvailabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # async def create(self, available: AvailabilityCreate, user: User):
    #     try:
    #         logging.info("Creando disponibilidad")
    #         sttmt_exist = select(Availability).where(Availability.date_all == available.date_all, Availability.user_id == user.id)
    #         available_exist: Availability | None = (await self.session.exec(sttmt_exist)).first()

    #         if available_exist is not None:
    #             return JSONResponse(
    #                 content={
    #                     "detail": "Ya existe la disponibilidad del día"
    #                     },
    #                 status_code=status.HTTP_400_BAD_REQUEST
    #             )
            
    #         new_available: Availability = Availability(** available.model_dump(), user_id= user.id,)

    #         self.session.add(new_available)
    #         await self.session.flush()

    #         slots: list[time]= await self.generate_time_slots(new_available.start_time, new_available.end_time)

    #         for slot in slots:
    #             new_appointment = Appointment(
    #                 date_get= new_available.date_all,
    #                 start_time= slot,
    #                 end_time = (datetime.combine(datetime.today(), slot) + timedelta(minutes=30)).time(),
    #                 user_id= user.id,
    #                 availability_id= new_available.id
    #             )
    #             self.session.add(new_appointment)

    #         if available.start_time_optional and available.end_time_optional:
    #             await self.session.flush()
    #             slots_optional: list[time]= await self.generate_time_slots(available.start_time_optional, available.end_time_optional)

    #             for slot in slots_optional:
    #                 new_appointment = Appointment(
    #                     date_get= new_available.date_all,
    #                     start_time= slot,
    #                     end_time = (datetime.combine(datetime.today(), slot) + timedelta(minutes=30)).time(),
    #                     user_id= user.id,
    #                     availability_id= new_available.id
    #                 )
    #                 self.session.add(new_appointment)
    #             await self.session.flush()

    #         await self.session.commit()

    #         logging.info("Disponibilidad creado!")

    #         return JSONResponse(
    #                 content={
    #                     "new_available": new_available.id
    #                     },
    #                 status_code=status.HTTP_201_CREATED
    #         )
    #     except Exception as e:
    #         logging.error(f"Error al crear disponibilidad: {e}")
    #         await self.session.rollback()
    #         raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear la disponibilidad")

    async def create(self, available: AvailabilityCreate, user: User):
        try:
            logging.info("Creando disponibilidad")

            # Verifica si ya existe una disponibilidad para la fecha y el usuario
            sttmt_exist = select(Availability).where(
                Availability.date_all == available.date_all,
                Availability.user_id == user.id
            )
            available_exist: Availability | None = (await self.session.exec(sttmt_exist)).first()

            if available_exist is not None:
                return JSONResponse(
                    content={"detail": "Ya existe la disponibilidad del día"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Crear la nueva disponibilidad
            new_available = Availability(**available.model_dump(), user_id=user.id)
            self.session.add(new_available)
            await self.session.flush()

            # Función auxiliar para crear turnos a partir de un rango horario
            async def create_appointments(start: time, end: time):
                slots: list[time] = await self.generate_time_slots(start, end)
                for slot in slots:
                    new_appointment = Appointment(
                        date_get=new_available.date_all,
                        start_time=slot,
                        end_time=(datetime.combine(datetime.today(), slot) + timedelta(minutes=30)).time(),
                        user_id=user.id,
                        availability_id=new_available.id
                    )
                    self.session.add(new_appointment)

            # Crear turnos para el horario principal
            await create_appointments(new_available.start_time, new_available.end_time)

            # Si hay horario adicional, crear también esos turnos
            if available.start_time_optional and available.end_time_optional:
                await create_appointments(available.start_time_optional, available.end_time_optional)

            await self.session.commit()
            logging.info("Disponibilidad creada!")

            return JSONResponse(
                content={"new_available": new_available.id},
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logging.error(f"Error al crear disponibilidad: {e}")
            await self.session.rollback()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Error al intentar crear la disponibilidad"
            )


    async def get_all(self, user_id: str, date_start: date = None, date_end: date = None):
        try:
            logging.info("Obteniendo Availabilities")
            if date_start is not None and date_end is not None:
                sttmt = select(Availability).where(
                    between(Availability.date_all, date_start, date_end)
                ).options(
                    joinedload(Availability.appointments)
                ).where(Availability.user_id == user_id)
            else: 
                sttmt = select(Availability
                            ).options(
                                joinedload(Availability.appointments)
                            ).where(Availability.user_id == user_id)
           
            availabilities: list[Availability] = (await self.session.exec(sttmt)).unique().all()

            list_availabilities: list[AvailabilityDto] = [
                AvailabilityDto(
                    id= avail.id,
                    date_all = avail.date_all,
                    start_time= avail.start_time,
                    end_time= avail.end_time,
                    start_time_optional= avail.start_time_optional,
                    end_time_optional= avail.end_time_optional,
                    disponibility = any(appointment.state == StateAppointment.NULL for appointment in avail.appointments),
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
        
    async def get(self, available_id: str, user_id: str):
        try:
            logging.info("Obteniendo disponibilidad")
            sttmt = select(Availability).options(
                    joinedload(Availability.appointments)
                ).where(
                    Availability.id == available_id,
                ).order_by(Availability.date_all.asc())
            
            exist_available: Availability | None = (await self.session.exec(sttmt)).first()

            if exist_available is None:
                return JSONResponse(
                    content={"detail": "Disponibilidad no encontrada"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            if exist_available.user_id != user_id:
                return JSONResponse(
                    content={"detail": "Disponibilidad erronea"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            exist_available.appointments.sort(key=lambda appt: appt.start_time)
            
            appointments_data = [AppointmentDto.model_validate(appointment).model_dump(mode='json') for appointment in exist_available.appointments]
            
            logging.info("Disponibilidad obtenida")

            return JSONResponse(
                content=AvailabilityResponseDto.model_validate({
                    **exist_available.model_dump(),
                    "appointments": appointments_data
                }).model_dump(mode='json'),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener disponibilidad: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener la disponibilidad"
            )
        
    # async def update(self, available_id: str, available_update: AvailabilityUpdate, user_id: str):
    #     try:
    #         logging.info("Actualizando disponibilidad")
    #         sttmt = select(Availability).options(
    #                 joinedload(Availability.appointments)
    #             ).where(Availability.id == available_id)
    #         available: Availability | None = (await self.session.exec(sttmt)).first()
            
    #         if available is None:
    #             return JSONResponse(
    #                 content={"detail": "Disponibilidad no encontrada"},
    #                 status_code=status.HTTP_404_NOT_FOUND
    #             )
            
    #         if available.user_id != user_id:
    #             return JSONResponse(
    #                 content={"detail": "No tiene permiso para eliminar disponibilidad"},
    #                 status_code=status.HTTP_403_FORBIDDEN
    #             )
            
    #         if available.date_all == date.today():
    #             return JSONResponse(
    #                 content={"detail": "No se puede modificar la fecha de hoy"},
    #                 status_code=status.HTTP_400_BAD_REQUEST
    #             )
            
    #         available.appointments.sort(key=lambda appt: appt.start_time)

    #         first_turn: Appointment | None = next((appt for appt in available.appointments if appt.state in [StateAppointment.PENDING, StateAppointment.ACCEPT]), None)
    #         last_turn: Appointment | None = next((appt for appt in reversed(available.appointments) if appt.state in [StateAppointment.PENDING, StateAppointment.ACCEPT]), None)
            
    #         # if available.start_time_optional and available.end_time_optional:
    #         #     first_turn_optional: Appointment | None = next((appt for appt in available.appointments if appt.state in [StateAppointment.PENDING, StateAppointment.ACCEPT] and appt.start_time == available.start_time_optional), None)
    #         #     last_turn_optional: Appointment | None = next((appt for appt in reversed(available.appointments) if appt.state in [StateAppointment.PENDING, StateAppointment.ACCEPT] and appt.start_time == available.end_time_optional), None)

    #         if first_turn is None and last_turn is None:
    #             available.start_time = available_update.start_time
    #             available.end_time = available_update.end_time

    #             for appointment in available.appointments:
    #                 await self.session.delete(appointment)

    #             slots: list[time]= await self.generate_time_slots(available_update.start_time, available_update.end_time)

    #             for slot in slots:
    #                 new_appointment = Appointment(
    #                     date_get= available.date_all,
    #                     start_time= slot,
    #                     end_time = (datetime.combine(datetime.today(), slot) + timedelta(minutes=30)).time(),
    #                     user_id= available.user_id,
    #                     availability_id= available.id
    #                 )
    #                 self.session.add(new_appointment)

    #             await self.session.commit()  

    #             logging.info("Disponibilidad actualizada")
    #             return JSONResponse(
    #                 content= {'detail': 'Disponibilidad editada con exito!'},
    #                 status_code=status.HTTP_200_OK
    #             )
            
    #         if available_update.start_time.replace(tzinfo=None) > first_turn.start_time or available_update.end_time.replace(tzinfo=None) < last_turn.end_time:
    #             return JSONResponse(
    #                 content={"detail": "No se puede modificar la hora de inicio o fin, revise los turnos pendientes o aceptados"},
    #                 status_code=status.HTTP_400_BAD_REQUEST
    #             )
            
    #         slots: list[time] = await self.generate_time_slots(available_update.start_time, available_update.end_time)
    #         appointment_save = []

    #         for appoint in available.appointments:
    #             if appoint.state in [StateAppointment.NULL, StateAppointment.CANCEL,StateAppointment.REJECT, StateAppointment.RESERVED]:
    #                 if appoint.state == StateAppointment.RESERVED:    
    #                     reason = "Se ha modificado la disponibilidad del día, por favor contactarte nuevamente con SIJAC, o enviar un nuevamente desde nuestra web"
    #                     await EmailService().send_email_client(StateAppointment.REJECT, appoint, reason)
    #                 await self.session.delete(appoint)
    #             else:
    #                 appointment_save.append(appoint.start_time)

    #         await self.session.flush()

    #         for slot in slots:
    #             if slot not in appointment_save:
    #                 new_appointment = Appointment(
    #                     date_get= available.date_all,
    #                     start_time= slot,
    #                     end_time = (datetime.combine(datetime.today(), slot) + timedelta(minutes=30)).time(),
    #                     user_id= user_id,
    #                     availability_id= available.id
    #                 )
    #                 self.session.add(new_appointment)

    #         available.start_time = available_update.start_time
    #         available.end_time = available_update.end_time

    #         await self.session.commit()  

    #         logging.info("Disponibilidad actualizada")
    #         return JSONResponse(
    #             content= {'detail': 'Disponibilidad editada con exito!'},
    #             status_code=status.HTTP_200_OK
    #         )
    #     except Exception as e:
    #         logging.error(f"Error al editar disponibilidad: {e}")
    #         await self.session.rollback()
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Error al intentar editar la disponibilidad"
    #         )

    async def update(self, available_id: str, available_update: AvailabilityUpdate, user_id: str):
        try:
            logging.info("Actualizando disponibilidad")
            sttmt = select(Availability).options(
                joinedload(Availability.appointments)
            ).where(Availability.id == available_id)
            available: Availability | None = (await self.session.exec(sttmt)).first()

            if available is None:
                return JSONResponse(
                    content={"detail": "Disponibilidad no encontrada"},
                    status_code=status.HTTP_404_NOT_FOUND
                )

            if available.user_id != user_id:
                return JSONResponse(
                    content={"detail": "No tiene permiso para editar disponibilidad"},
                    status_code=status.HTTP_403_FORBIDDEN
                )

            if available.date_all == date.today():
                return JSONResponse(
                    content={"detail": "No se puede modificar la fecha de hoy"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            available.appointments.sort(key=lambda appt: appt.start_time)

            active_appts = [
                appt for appt in available.appointments
                if appt.state in [StateAppointment.PENDING, StateAppointment.ACCEPT]
            ]

            if not active_appts:
                # No hay turnos activos, se puede actualizar todo y recrear
                available.start_time = available_update.start_time
                available.end_time = available_update.end_time
                available.start_time_optional = available_update.start_time_optional
                available.end_time_optional = available_update.end_time_optional

                for appointment in available.appointments:
                    await self.session.delete(appointment)

                # Generar nuevos slots de ambos rangos si se proveen
                slots: list[time] = []
                slots += await self.generate_time_slots(available_update.start_time, available_update.end_time)

                if available_update.start_time_optional and available_update.end_time_optional:
                    slots += await self.generate_time_slots(available_update.start_time_optional, available_update.end_time_optional)

                for slot in slots:
                    new_appointment = Appointment(
                        date_get=available.date_all,
                        start_time=slot,
                        end_time=(datetime.combine(datetime.today(), slot) + timedelta(minutes=30)).time(),
                        user_id=available.user_id,
                        availability_id=available.id
                    )
                    self.session.add(new_appointment)

                await self.session.commit()

                logging.info("Disponibilidad actualizada")
                return JSONResponse(
                    content={'detail': 'Disponibilidad editada con éxito!'},
                    status_code=status.HTTP_200_OK
                )

            # Validar si los turnos activos están dentro del nuevo horario
            updated_ranges = [
                (available_update.start_time, available_update.end_time)
            ]
            if available_update.start_time_optional and available_update.end_time_optional:
                updated_ranges.append((available_update.start_time_optional, available_update.end_time_optional))

            for appt in active_appts:
                if not any(start <= appt.start_time <= end for start, end in updated_ranges):
                    return JSONResponse(
                        content={"detail": f"No se puede modificar el horario. Existen turnos activos fuera del nuevo rango: {appt.start_time.strftime('%H:%M')}"},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            # Eliminar turnos no activos
            appointment_save = []
            for appoint in available.appointments:
                if appoint.state in [StateAppointment.NULL, StateAppointment.CANCEL, StateAppointment.REJECT, StateAppointment.RESERVED]:
                    if appoint.state == StateAppointment.RESERVED:
                        reason = "Se ha modificado la disponibilidad del día, por favor contactarte nuevamente con SIJAC, o enviar un turno nuevo desde nuestra web"
                        await EmailService().send_email_client(StateAppointment.REJECT, appoint, reason)
                    await self.session.delete(appoint)
                else:
                    appointment_save.append(appoint.start_time)

            await self.session.flush()

            # Crear nuevos turnos para los slots que no existan aún
            slots: list[time] = []
            slots += await self.generate_time_slots(available_update.start_time, available_update.end_time)

            if available_update.start_time_optional and available_update.end_time_optional:
                slots += await self.generate_time_slots(available_update.start_time_optional, available_update.end_time_optional)

            for slot in slots:
                if slot not in appointment_save:
                    new_appointment = Appointment(
                        date_get=available.date_all,
                        start_time=slot,
                        end_time=(datetime.combine(datetime.today(), slot) + timedelta(minutes=30)).time(),
                        user_id=user_id,
                        availability_id=available.id
                    )
                    self.session.add(new_appointment)

            available.start_time = available_update.start_time
            available.end_time = available_update.end_time
            available.start_time_optional = available_update.start_time_optional
            available.end_time_optional = available_update.end_time_optional

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

        
    async def delete(self, available_id: str, user_id: str):
        try:
            logging.info("Eliminando disponibilidad")
            sttmt = select(Availability).options(
                joinedload(Availability.appointments)
            ).where(Availability.id == available_id)
            available: Availability | None = (await self.session.exec(sttmt)).first()

            available: Availability | None = await self.session.get(Availability, available_id)
            
            if available is None:
                return JSONResponse(
                    content={"detail": "Disponibilidad no encontrada"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            if available.user_id != user_id:
                return JSONResponse(
                    content={"detail": "No tiene permiso para eliminar disponibilidad"},
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            for appointment in available.appointments:
                if appointment.state == StateAppointment.PENDING or appointment.state == StateAppointment.ACCEPT:
                    reason = "Se ha eliminado la disponibilidad del día, por favor contactarte nuevamente con SIJAC, o enviar un nuevamente desde nuestra web"
                    await EmailService().send_email_client(StateAppointment.REJECT, appointment, reason)
                await self.session.delete(appointment)
            
            await self.session.delete(available)

            await self.session.commit()

            logging.info("Disponibilidad eliminada")

            JSONResponse(
                content= {"detail": "Disponibilidad eliminada con exito!"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al eliminar Disponibilidad: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar eliminar disponibilidad"
            )
        
    async def generate_time_slots(self, start_time: time, end_time: time, interval_minutes: int = 30):
        slots = []
        current_time = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)

        while current_time+timedelta(minutes=interval_minutes) <= end_datetime:
            slots.append(current_time.time())  
            current_time += timedelta(minutes=interval_minutes)  

        return slots