from datetime import datetime
import logging
import os
import shutil
from decouple import config

async def backup_database():
    try:
        os.makedirs(config('BACKUP_FOLDER'), exist_ok=True)
        # Crear nombre de archivo con fecha/hora
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(config('BACKUP_FOLDER'), f"sijac_backup_{timestamp}.db")

        # Copiar la base de datos
        shutil.copy(config('DB_PATH'), backup_file)

        logging.info(f"📂 Copia de seguridad creada: {backup_file}")
    except Exception as e:
        logging.error(f"❌ Error al hacer la copia de seguridad: {e}")