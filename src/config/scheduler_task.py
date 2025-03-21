import logging
from sqlmodel import select
from src.database.db import db
from src.drive.backup.backup_db import drive_backup_db
from src.drive.backup.backup_images import drive_backup_images
from src.models.appointment import Appointment, StateAppointment
from datetime import date

async def backup_database():
    try:
        logging.info(f"Realizando backup de la base de datos")
        async for session in db.get_session():
            try:
                sttmt = select(Appointment
                            ).where(Appointment.state == StateAppointment.NULL
                            ).where(Appointment.date_get < date.today()
                        )
                appointments: list[Appointment] = (await session.exec(sttmt)).all()
                for appointment in appointments:
                    await session.delete(appointment)
                break
            except Exception as e:
                logging.error(f"Error al eliminar citas antiguas: {e}")
                break 

        await drive_backup_db()

        await drive_backup_images()
    except Exception as e:
        logging.error(f"Error al hacer la copia de seguridad: {e}")