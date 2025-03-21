from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.config.init_data import init_data
from src.config.logging_config import setup_logging
from src.config.scheduler_task import backup_database
from src.middleware.timing import TimingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from src.database.db import db
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.routers.user_router import user_router
from src.routers.blog_router import blog_router
from src.routers.email_router import email_router
from src.routers.image_router import image_router
from src.routers.availability_router import availability_router
from src.routers.appointment_router import appointment_router

setup_logging()

app = FastAPI(title= 'API SIJAC',
            description='API SIJAC',
            version='0.0.1',
            docs_url='/',
            )

app.include_router(router= user_router)
app.include_router(router= blog_router)
app.include_router(router= email_router)
app.include_router(router= image_router)
app.include_router(router= availability_router)
app.include_router(router= appointment_router)

origins = [
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TimingMiddleware)

scheduler = AsyncIOScheduler()

# scheduler.add_job(backup_database, CronTrigger(day_of_week="thu", hour=20, minute=43))
scheduler.add_job(backup_database, CronTrigger(day_of_week="sun", hour=1, minute=0))

@asynccontextmanager
async def lifespan(app: FastAPI):
    if db.is_closed():
        try:
            # await db.create_database_if_not_exists()   #QUITAR ESTA LINEA PARA MYSQL
            await db.connect()
        except Exception as e:
            logging.error(f"Error al conectar a la base de datos: {e}")
            raise e
    await db.create_tables()
    async for session in db.get_session():
        await init_data(session)
        break

    scheduler.start()
    logging.info("🚀 Scheduler iniciado")
    yield
    if not db.is_closed():
        await db.close()
        logging.info("El servidor se está cerrando.")


app.router.lifespan_context = lifespan
