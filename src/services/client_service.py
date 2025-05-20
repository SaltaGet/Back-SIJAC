from datetime import date, datetime, timedelta
import json
import logging
import asyncio
from fastapi import HTTPException, status
from src.config.timezone import get_timezone
from src.models.appointment import Appointment, StateAppointment
from sqlmodel import between, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.models.audit import Audit
from src.models.client import Client
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.appointment_schema.appointment_response import AppointmentResponse
from src.schemas.client.client_create import ClientCreate
from src.schemas.client.client_response import ClientResponse
from src.schemas.client.client_update import ClientUpdate
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
import copy


class ClientService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, client_create: ClientCreate, user_id: str):
        try:
            logging.info("Creando cliente")
            
            new_client: Client = Client(**client_create.model_dump())

            self.session.add(new_client)


            await self.session.flush()

            self.session.add(Audit(
                user_id= user_id,
                method= "CREATE",
                old_data= "",
                new_data= new_client.model_dump(mode='json'),
            ))

            await self.session.commit()

            logging.info("Cliente creado!")

            return JSONResponse(
                content={
                    "client_id": new_client.id
                    },
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logging.error(f"Error al crear cliente: {e}")
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear el cliente")

    async def get_all(self):
        try:
            logging.info("Obteniendo Clientes")
            sttmt = select(Client)
           
            clients: list[Client] = (await self.session.exec(sttmt)).all()

            list_clients: list[ClientResponse] = [
                ClientResponse.model_validate(client).model_dump(mode='json')
                for client in clients
            ]
            logging.info("Clientes obtenidos")

            return JSONResponse(
                content= list_clients,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener Clientes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener Clientes"
            )
        
    async def get(self, client_id: str):
        try:
            logging.info("Obteniendo turno")
            sttmt = select(Client).where(Client.id == client_id)
            client: Client | None = (await self.session.exec(sttmt)).first()

            if client is None:
                return JSONResponse(
                    content={"detail": "Cliente no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return JSONResponse(
                content=ClientResponse.model_validate(client).model_dump(mode='json'),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener cliente: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el cliente"
            )
        
    async def get_by_dni(self, dni: str, user_id: str):
        try:
            logging.info("Obteniendo clientes")
            sttmt = select(Client).where(Client.dni.like(f"%{dni}%"))
            clients: list[Client] = (await self.session.exec(sttmt)).all()

            list_clients: list[ClientResponse] = [
                ClientResponse.model_validate(client).model_dump(mode='json')
                for client in clients
            ]

            logging.info("Clientes obtenidos con exito")
            
            return JSONResponse(
                content=list_clients,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener clientes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener los clientes"
            )
        
    async def get_by_name(self, name: str):
        try:
            logging.info("Obteniendo clientes")
            sttmt = select(Client).where(
                or_(
                    Client.first_name.like(f"%{name}%"),
                    Client.last_name.like(f"%{name}%")
                )
            )
            clients: list[Client] = (await self.session.exec(sttmt)).all()

            list_clients: list[ClientResponse] = [
                ClientResponse.model_validate(client).model_dump(mode='json')
                for client in clients
            ]

            logging.info("Clientes obtenidos con exito")
            
            return JSONResponse(
                content=list_clients,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener clientes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener los clientes"
            )
        
    async def update(self, client_id: str, client_udpate: ClientUpdate, user_id: str):
        try:
            logging.info("Obteniendo cliente")
            sttmt = select(Client).where(Client.id == client_id)
            client: Client | None = (await self.session.exec(sttmt)).first()

            if client is None:
                return JSONResponse(
                    content={"detail": "Cliente no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            client_copy = copy.deepcopy(client)
            
            client.first_name = client_udpate.first_name
            client.last_name = client_udpate.last_name
            client.email = client_udpate.email
            client.phone = client_udpate.phone
            client.updated_at = get_timezone()

            self.session.add(Audit(
                user_id= user_id,
                method= "UPDATE",
                old_data= json.dumps(client_copy.model_dump(mode='json')),
                new_data= json.dumps(client.model_dump(mode='json')),
            ))

            await self.session.commit()

            logging.info("Cliente actualizado")


            return JSONResponse(
                content= {'detail': 'Cliente editado con exito!'},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al editar Cliente: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar editar Cliente"
            )
        
   