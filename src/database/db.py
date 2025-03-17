from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from decouple import config
import logging
import aiosqlite

class DataBase:
    def __init__(self):
        self.database_url = f"sqlite+aiosqlite:///./{config('DB_NAME')}.db"
        self.engine = create_async_engine(self.database_url, echo=True)

    async def connect(self):
        try:
            logging.info('Conectando a la base de datos...')
            await self.engine.connect()
            logging.info('Conexión exitosa')
        except Exception as e:
            logging.error(f'Error al conectar a la base de datos: {e}')
            raise e

    async def close(self):
        logging.info('Cerrando conexion a la base de datos...')
        await self.engine.dispose()
        logging.info('Conexión cerrada')

    def is_closed(self):
            return self.engine.pool is None or self.engine.pool.status() == 'closed'

    async def create_tables(self):
        try:
            logging.info('Validando tablas...')
            from src.models.user_model import User
            from src.models.blog_model import Blog
            from src.models.refresh_token import HistorialRefreshToken
            from src.models.availability import Availability
            from src.models.appointment import Appointment

            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logging.info('Tablas validadas')
        except Exception as e:
            logging.error(f'Error al validar las tablas: {e}')
            raise e

    async def get_session(self):
        async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            yield session


db = DataBase()