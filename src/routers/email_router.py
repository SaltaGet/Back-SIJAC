from fastapi import APIRouter
from src.schemas.user_schema.email_contact import EmailContact
from src.services.email_service import EmailService

email_router = APIRouter(prefix='/email', tags=['Email'])

@email_router.post('/send_mail')
async def send_mail(
    contact: EmailContact
):
    return await EmailService().send_email(contact)