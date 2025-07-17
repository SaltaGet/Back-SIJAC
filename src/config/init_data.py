import os
import logging
import io
from fastapi import UploadFile
from src.models.user_model import RoleUser
from src.schemas.user_schema.user_create import UserCreate
from src.services.user_service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
import aiofiles
from decouple import config

async def init_data(session: AsyncSession):
    try:
        logging.info("Creando usuario admin.")
        user_admin = UserCreate(
            username=config('ADMIN_USERNAME'),
            email=config('ADMIN_EMAIL'),
            password_hash=config('ADMIN_PASS'),
            first_name=config('ADMIN_FIRSTNAME'),
            last_name=config('ADMIN_LASTNAME'),
            specialty=config('ADMIN_SPECIALITY')
        )
        
        user_secretary = UserCreate(
            username=config('SECRETARY_USERNAME'),
            email=config('SECRETARY_EMAIL'),
            password_hash=config('SECRETARY_PASS'),
            first_name=config('SECRETARY_FIRSTNAME'),
            last_name=config('SECRETARY_LASTNAME'),
            specialty=config('SECRETARY_SPECIALITY')
        )

        image_path = os.path.join('src', 'static', 'image', 'admin_user.png')
        upload_file = await create_upload_file(image_path)

        response = await UserService(session).create_user(user_admin, upload_file, RoleUser.ADMIN)

        if response.status_code == 409:
            logging.info("Usuario admin ya existe")
            return False

        if response.status_code == 201:
            logging.info("Usuario admin creado con éxito")
        
            image_recepcion = os.path.join('src', 'static', 'image', 'recepcion.png')
            upload_file_secretary = await create_upload_file(image_recepcion)
            response = await UserService(session).create_user(user_secretary, upload_file_secretary, RoleUser.SECRETARY)

            if response.status_code == 409:
                logging.info("Usuario secretary ya existe")
                return False

            if response.status_code == 201:
                logging.info("Usuario secretary creado con éxito")
                return True
        
        return None
    except Exception as e:
        logging.error(f"Error al crear usuario admin: {str(e)}")
        return None

async def create_upload_file(file_path: str) -> UploadFile:
    async with aiofiles.open(file_path, 'rb') as f:
        contents = await f.read()
        upload_file = UploadFile(
            filename=os.path.basename(file_path),
            file=io.BytesIO(contents)
        )
        # Establecer headers para content_type
        upload_file.headers = {'content-type': 'image/png'}
        return upload_file



# 
#import base64
# import io
# import os
# import logging
# from fastapi import UploadFile
# from fastapi import UploadFile
# from src.schemas.user_schema.user_create import UserCreate
# from src.services.user_service import UserService
# from sqlmodel.ext.asyncio.session import AsyncSession
# from pathlib import Path
# import aiofiles

# async def init_data(session: AsyncSession):
#     try:
#         logging.info("Creando usuario admin.")
#         user_admin = UserCreate(
#             username= 'Admin',
#             email= 'admin@sijac.com',
#             password_hash= 'Sijac2025!',
#             first_name= 'Consultora',
#             last_name= 'SIJAC',
#             specialty= "Admin"
#         )

#         image_path = os.path.join('src', 'static', 'image', 'admin_user.png')

#         upload_file = await create_upload_file(image_path)

#         # Establecer el content_type manualmente (opcional pero recomendado)
#         upload_file.content_type = "image/png" 
#         response =  await UserService(session).create_user(user_admin, True, upload_file)

#         if response.status_code == 409:
#             logging.info("Usuario admin ya existe")
#             return False

#         if response.status_code == 201:
#             logging.info("Usuario admin creado con exito")
#             return True
        
#         return None
#     except Exception as e:
#         return None
    
# async def create_upload_file(file_path: str):
#     async with aiofiles.open(file_path, "rb") as f:
#         contents = await f.read()
#         return UploadFile(
#             filename=os.path.basename(file_path),
#             file=io.BytesIO(contents),
#             content_type="image/png" 
#         )