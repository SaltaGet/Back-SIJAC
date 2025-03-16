import logging
from sqlmodel import select
from src.models.user_model import User
from src.schemas.user_schema.user_create import UserCreate
from src.services.user_service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession


async def init_data(session: AsyncSession):
    try:
        logging.info("Creando usuario admin.")
        user_admin = UserCreate(
            username= 'Admin',
            email= 'admin@convivir.com',
            password_hash= 'FundConvivir25!',
            first_name= 'Fundación',
            last_name= 'Convivir',
        )

        response =  await UserService(session).create_user(user_admin, True)

        if response.status_code == 409:
            logging.info("Usuario admin ya existe")
            return False

        if response.status_code == 201:
            logging.info("Usuario admin creado con exito")
            return True
        
        return None
    except Exception as e:
        return None