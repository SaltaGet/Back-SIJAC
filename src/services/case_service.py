from datetime import date, datetime, timedelta
import logging
import asyncio
from fastapi import HTTPException, status
from src.config.timezone import get_timezone
from src.models.appointment import Appointment, StateAppointment
from sqlmodel import between, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.models.case import Case, StateCase
from src.models.user_case import UserCase, TypePermision
from src.models.user_case import UserCase
from src.models.user_model import User
from src.schemas.appointment_schema.appointment_crate import AppointmentCreate
from src.schemas.appointment_schema.appointment_response import AppointmentResponse
from src.schemas.case.case_create import CaseCreate
from src.schemas.case.case_dto import CaseResponseDTO
from src.schemas.case.case_response import CaseResponse
import copy
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from src.schemas.case.case_update import CaseUpdate
from src.schemas.client.client_dto import ClientResponseDTO
from src.schemas.client.client_response import ClientResponse
from src.schemas.user_schema.user_response import UserResponse


class CaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, case_create: CaseCreate, user_id :str):
        try:
            logging.info("Creando cliente")
            
            new_case: Case = Case(**case_create.model_dump())

            self.session.add(new_case)

            await self.session.flush()

            self.session.add(UserCase(
                user_id= user_id,
                case_id= new_case.id,
                permision= TypePermision.PRINCIPAL,
            ))

            await self.session.commit()

            logging.info("Caso creado!")

            return JSONResponse(
                content={
                    "case_id": new_case.id
                    },
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logging.error(f"Error al crear caso: {e}")
            await self.session.rollback()
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear el caso")

    async def get_all(self, user_id :str):
        try:
            logging.info("Obteniendo Casos")
            sttmt = (
                select(Case)
                .join(UserCase, UserCase.case_id == Case.id)
                .where(UserCase.user_id == user_id)
                .options(
                    joinedload(Case.client),
                    joinedload(Case.users)
                )
            )

            cases: list[Case] = (await self.session.exec(sttmt)).unique().all()
            list_cases: list[CaseResponseDTO] = []

            for case in cases:
                owner = False
                for user in case.users:
                    if user.user_id == user_id:
                        owner= user.permision == TypePermision.PRINCIPAL
                        break
                list_cases.append(CaseResponseDTO(
                        id= case.id,
                        detail= case.detail,
                        state= case.state,
                        client= ClientResponseDTO(
                            id= case.client.id,
                            first_name= case.client.first_name,
                            last_name= case.client.last_name
                            ).model_dump(mode='json'),
                        owner= owner,
                        created_at= case.created_at,
                        updated_at= case.updated_at,
                    ).model_dump(mode='json')
                )

            logging.info("Casos obtenidos")

            return JSONResponse(
                content= list_cases,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener Casos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener Casos"
            )
        
    async def get(self, case_id: str, user_id: str):
        try:
            logging.info("Obteniendo Caso")
            # sttmt = (
            #     select(Case)
            #     .join(UserCase, UserCase.case_id == Case.id)
            #     .where(Case.id == case_id)
            #     .where(UserCase.user_id == user_id)
            #     .options(
            #         joinedload(Case.client),
            #         joinedload(Case.users)
            #     )
            # )
            sttmt = (
                select(Case)
                .join(UserCase, UserCase.case_id == Case.id)
                .where(UserCase.user_id == user_id)
                .options(
                    selectinload(Case.client),
                    selectinload(Case.users).selectinload(UserCase.user)  # si `users` es relación intermedia
                )
            )
            case: Case | None = (await self.session.exec(sttmt)).first()

            if case is None:
                return JSONResponse(
                    content={"detail": "Caso no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            owner = False
            for user in case.users:
                if user.user_id == user_id:
                    owner= user.permision == TypePermision.PRINCIPAL
                    break
            
            case_response = CaseResponse(
                id=case.id,
                detail=case.detail,
                state=case.state,
                # client=ClientResponse.model_validate(case.client),
                client=ClientResponse(**case.client.model_dump()).model_dump(mode='json'),
                owner= owner,
                created_at=case.created_at,
                updated_at=case.updated_at,
                # users=[UserResponse.model_validate(uc.user) for uc in case.users] if case.users else []
                users=[UserResponse(**uc.user.model_dump()).model_dump(mode='json') for uc in case.users] if case.users else []
            )
            
            return JSONResponse(
                content= case_response.model_dump(mode='json'),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener caso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el caso"
            )
        
    async def get_by_client(self, client_id: str, user_id: str):
        try:
            logging.info("Obteniendo casos")
            sttmt = (
                select(Case)
                .join(UserCase, UserCase.case_id == Case.id)
                .where(Case.client_id == client_id)
                .where(UserCase.user_id == user_id)
                .options(
                    joinedload(Case.client),
                    joinedload(Case.users)
                )
            )
            cases: list[Case] = (await self.session.exec(sttmt)).unique().all()

            # list_cases: list[CaseResponseDTO] = [
            #     CaseResponseDTO(
            #         id=case.id,
            #         detail=case.detail,
            #         state=case.state,
            #         client=ClientResponseDTO(
            #             id=case.client.id if case.client else None,
            #             first_name=case.client.first_name if case.client else None,
            #             last_name=case.client.last_name if case.client else None
            #         ),
            #         created_at=case.created_at,
            #         updated_at=case.updated_at,
            #     ).model_dump(mode='json')
            #     for case in cases
            # ]

            list_cases: list[CaseResponseDTO] = []

            for case in cases:
                owner = False
                for user in case.users:
                    if user.user_id == user_id:
                        owner= user.permision == TypePermision.PRINCIPAL
                        break
                list_cases.append(CaseResponseDTO(
                        id= case.id,
                        detail= case.detail,
                        state= case.state,
                        client= ClientResponseDTO(
                            id= case.client.id,
                            first_name= case.client.first_name,
                            last_name= case.client.last_name
                            ).model_dump(mode='json'),
                        owner= owner,
                        created_at= case.created_at,
                        updated_at= case.updated_at,
                    ).model_dump(mode='json')
                )

            logging.info("Casos obtenidos con exito")
            
            return JSONResponse(
                content=list_cases,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener casos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener los casos"
            )
        
    async def get_by_state(self, state: StateCase, user_id: str):
        try:
            logging.info("Obteniendo casos")
            # sttmt = (
            #     select(Case)
            #     .join(UserCase, UserCase.case_id == Case.id)
            #     .where(Case.state == state)
            #     .where(UserCase.user_id == user_id)
            #     .options(
            #         joinedload(Case.client),
            #         joinedload(Case.users)
            #     )
            # )
            sttmt = (
                select(Case)
                .join(UserCase, UserCase.case_id == Case.id)
                .where(UserCase.user_id == user_id)
                .options(
                    selectinload(Case.client),
                    selectinload(Case.users).selectinload(UserCase.user)  # si `users` es relación intermedia
                )
            )
            cases: list[Case] = (await self.session.exec(sttmt)).all()

            # list_cases: list[CaseResponseDTO] = [
            #     CaseResponseDTO(
            #         id=case.id,
            #         detail=case.detail,
            #         state=case.state,
            #         client=ClientResponseDTO(
            #             id=case.client.id if case.client else None,
            #             first_name=case.client.first_name if case.client else None,
            #             last_name=case.client.last_name if case.client else None
            #         ),
            #         created_at=case.created_at,
            #         updated_at=case.updated_at,
            #     ).model_dump(mode='json')
            #     for case in cases
            # ]

            list_cases: list[CaseResponseDTO] = []

            for case in cases:
                owner = False
                for user in case.users:
                    if user.user_id == user_id:
                        owner= user.permision == TypePermision.PRINCIPAL
                        break
                list_cases.append(CaseResponseDTO(
                        id= case.id,
                        detail= case.detail,
                        state= case.state,
                        client= ClientResponseDTO(
                            id= case.client.id,
                            first_name= case.client.first_name,
                            last_name= case.client.last_name
                            ).model_dump(mode='json'),
                        owner= owner,
                        created_at= case.created_at,
                        updated_at= case.updated_at,
                    ).model_dump(mode='json')
                )

            logging.info("Casos obtenidos con exito")
            
            return JSONResponse(
                content=list_cases,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener casos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener los casos"
            )
        
    async def update(self, case_id: str, client_udpate: CaseUpdate, user_id: str):
        try:
            logging.info("Obteniendo clientes")
            sttmt = (
                select(Case)
                .join(UserCase, UserCase.case_id == Case.id)
                .where(Case.id == case_id)
                .where(UserCase.user_id == user_id)
            )
            case: Case | None = (await self.session.exec(sttmt)).first()

            if case is None:
                return JSONResponse(
                    content={"detail": "Caso no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            case.detail = client_udpate.detail
            case.state = client_udpate.state
            await self.session.commit()

            logging.info("Caso editado con exito")
            
            return JSONResponse(
                content= {"detail": "Caso actualizado"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener caso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el caso"
            )
        
    async def update_state(self, case_id: str, state: StateCase, user_id: str):
        try:
            logging.info("Obteniendo clientes")
            sttmt = (
                select(Case)
                .join(UserCase, UserCase.case_id == Case.id)
                .where(Case.id == case_id)
                .where(UserCase.user_id == user_id)
            )
            case: Case | None = (await self.session.exec(sttmt)).first()

            if case is None:
                return JSONResponse(
                    content={"detail": "Caso no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            case.state = state
            await self.session.commit()

            logging.info("Caso editado con exito")
            
            return JSONResponse(
                content= {"detail": "Caso actualizado"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener caso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el caso"
            )
        
    async def share_case(self, case_id: str, user_share: str, user_id: str):
        try:
            logging.info("Obteniendo caso")
            sttmt = (
                select(UserCase)
                .where(UserCase.case_id == case_id)
                .where(UserCase.user_id == user_id)
                .where(UserCase.permision == TypePermision.PRINCIPAL)
            )
            case: Case | None = (await self.session.exec(sttmt)).first()

            if case is None:
                return JSONResponse(
                    content={"detail": "Caso no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            sttmt_exist = (
                select(UserCase)
                .where(UserCase.case_id == case_id)
                .where(UserCase.user_id == user_share)
                .where(UserCase.permision == TypePermision.SECONDARY)
            )
            case_exist: UserCase | None = (await self.session.exec(sttmt_exist)).first()

            if case_exist is not None:
                return JSONResponse(
                    content={"detail": "Caso ya compartido"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            self.session.add(UserCase(
                user_id= user_share,
                case_id= case_id,
                permision= TypePermision.SECONDARY,
            ))
            
            await self.session.commit()

            logging.info("Caso compartido con exito")
            
            return JSONResponse(
                content= {"detail": "Caso compartido"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al compartir caso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar compartir el caso"
            )
        
    async def unshare_case(self, case_id: str, user_unshare: str, user_id: str):
        try:
            logging.info("Obteniendo caso")
            sttmt = (
                select(UserCase)
                .where(Case.id == case_id)
                .where(UserCase.user_id == user_id)
                .where(UserCase.permision == TypePermision.PRINCIPAL)
            )
            case: Case | None = (await self.session.exec(sttmt)).first()

            if case is None:
                return JSONResponse(
                    content={"detail": "Caso no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            sttmt_exist = (
                select(UserCase)
                .where(UserCase.case_id == case_id)
                .where(UserCase.user_id == user_unshare)
                .where(UserCase.permision == TypePermision.SECONDARY)
            )
            case_exist: UserCase | None = (await self.session.exec(sttmt_exist)).first()

            if case_exist is None:
                return JSONResponse(
                    content={"detail": "Caso no compartido"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            await self.session.delete(case_exist)
            
            await self.session.commit()

            logging.info("Caso compartido eliminado con exito")
            
            return JSONResponse(
                content= {"detail": "Caso compartido eliminado"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al eliminar caso compartido: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar eliminar el caso compartido"
            )
        
    async def delete(self, case_id: str, user_id: str):
        try:
            logging.info("Obteniendo caso")
            sttmt = (
                select(Case)
                .join(UserCase, UserCase.case_id == Case.id)
                .where(Case.id == case_id)
                .where(UserCase.user_id == user_id)
                .where(UserCase.permision == TypePermision.PRINCIPAL)
            )
            case: Case | None = (await self.session.exec(sttmt)).first()

            if case is None:
                return JSONResponse(
                    content={"detail": "Caso no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            sttmt_shared = select(UserCase).where(UserCase.case_id == case.id)
            cases_shared: List[UserCase] = (await self.session.exec(sttmt_shared)).unique().all()

            for case_shared in cases_shared:
                await self.session.delete(case_shared)
            
            await self.session.delete(case)
            
            await self.session.commit()

            logging.info("Caso eliminado con exito")
            
            return JSONResponse(
                content= {"detail": "Caso eliminado"},
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al eliminar caso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar eliminar el caso"
            )