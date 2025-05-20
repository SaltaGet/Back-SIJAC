import base64
import logging
import os
from typing import List
import zlib
from fastapi import HTTPException, Request, status, UploadFile
from src.config.timezone import get_timezone
from src.models.audit import Audit
from src.models.blog_model import Blog
from sqlmodel import desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from src.schemas.blog_schemas.blog_create import BlogCreate
from src.schemas.blog_schemas.blog_response import BlogResponse
from src.schemas.blog_schemas.blog_update import BlogUpdate
from src.schemas.user_schema.user_response import UserResponse
from src.services.image_service import ImageTool


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, page: int = 1, per_page: int = 9):
        try:
            logging.info("Obteniendo audits paginados")
            offset = (page - 1) * per_page
            
            sttmt = (
                select(Audit)
                .order_by(desc(Audit.created_at))
                .limit(per_page)
                .offset(offset)
            )
            
            audits: List[Audit] = (await self.session.exec(sttmt)).unique().all()

            sttmt_total = select(func.count(Audit.id))
            total_audits = (await self.session.exec(sttmt_total)).first()
            
            list_blogs: List[BlogResponse] = [audit.model_dump(mode='json') for audit in audits]

            logging.info("Audits obtenidos correctamente")
            
            return JSONResponse(
                content={
                    "page": page,
                    "per_page": per_page,
                    "total": len(audits),
                    "total_pages": (total_audits // per_page) + 1 if total_audits > 0 else 0,
                    "data": list_blogs
                },
                status_code=200
            )
        except Exception as e:
            logging.error(f"Error al obtener Audits: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error al intentar obtener los Audits"
            )
        
    async def get(self, audit_id: str):
        try:
            logging.info("Obteniendo blog")
            sttmt = select(Audit).options(
                    joinedload(Audit.user)
                ).where(
                    Audit.id == audit_id,
                )
           
            audit: Audit | None = (await self.session.exec(sttmt)).first()

            if audit is None:
                return JSONResponse(
                    content={"detail": "Audit no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            user_data = UserResponse.model_validate(audit.user).model_dump(mode='json')
            audit_data = audit.model_dump(mode='json')
           
            logging.info("Audit obtenido")

            return JSONResponse(
                content={
                    "audit": audit_data,
                    "user": user_data
                },
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logging.error(f"Error al obtener blog: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener el blog"
            )