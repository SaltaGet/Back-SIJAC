import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
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
            message = MIMEMultipart()
            message['From'] = email_contact.from_email or self.username
            message['To'] = email_contact.to_email
            message['Subject'] = email_contact.subject

            html_body = f"""
                <html>
                <head>
                </head>
                <body>
                    <h1>{email_contact.subject}</h1>
                    <p>{email_contact.body}</p>
                    <p class="important">Este es un mensaje importante con formato HTML y estilos.</p>
                </body>
                </html>
                """

            message.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.port) as server:
                try:
                    server.starttls()
                    server.login(self.email, self.password)
                    server.send_message(message)
                except smtplib.SMTPException as e:
                    print(f"Error sending email: {e}")
                    raise
        except Exception as e:
            print(e)
            raise