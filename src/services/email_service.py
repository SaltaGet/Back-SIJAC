import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

from src.schemas.user_schema.email_contact import EmailContact

class EmailService:
    def __init__(self):
        self.smtp_server = config('SMTP_SERVER')
        self.port = config('EMAIL_PORT')
        self.email = config('EMAIL')
        self.password = config('EMAIL_PASSWORD')

    async def send_email(
        self,
        email_contact: EmailContact
    ) -> None:
        try:
            logging.info("Enviando email")
            message_convivir = MIMEMultipart()
            message_convivir['From'] = self.email
            message_convivir['To'] = self.email
            message_convivir['Subject'] = f"Contacto {email_contact.subject}"

            message_to = MIMEMultipart()
            message_to['From'] = self.email
            message_to['To'] = email_contact.email
            message_to['Subject'] = 'SIJAC'

            html_convivir = f"""
                <html>
                <head>
                </head>
                <body style="padding: 40px;">
                    <h2>Datos de Contacto</h2>
                    <p style="text-indent: 40px;"><strong>Nombre: </strong>{email_contact.full_name}</p>
                    <p style="text-indent: 40px;"><strong>Teléfono: </strong>{email_contact.cellphone}</p>
                    <p style="text-indent: 40px;"><strong>Email: </strong> {email_contact.email}</p>

                    <h3>Motivo:</h3>
                    <p style="text-indent: 40px;">{email_contact.body}</p>
                </body>
                </html>
                """
            
            html_to = f"""
                <html>
                <head>
                </head>
                <body style="padding: 40px;">
                    <h2 style="text-align: center;">Hola {email_contact.full_name}!!!</h2>
                    <p style="text-align: start;">Usted ha comunicado con nosotros por el siguiente motivo:</p>
                    <p style="text-align: center; margin: 20px 40px 20px 40px; font-style: italic;">"{email_contact.body}"</p>
                    <p style="text-align: center;">Nos pondremos en contacto contigo lo mas antes posible.</p>
                    <h2 style="text-align: center;">Gracias por contacarte con SIJAC!!!</h2>
                </body>
                </html>
                """

            message_convivir.attach(MIMEText(html_convivir, 'html'))
            message_to.attach(MIMEText(html_to, 'html'))

            with smtplib.SMTP(self.smtp_server, self.port) as server:
                try:
                    server.starttls()
                    server.login(self.email, self.password)
                    server.send_message(message_to)
                    server.send_message(message_convivir)
                    logging.info("Email enviado")
                except smtplib.SMTPException as e:
                    logging.error(f"Error sending email: {e}")
                    raise
        except Exception as e:
            logging.error(f"Error al enviar email")
            raise