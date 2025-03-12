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
        # attachments: Optional[list[str]] = None
    ) -> None:
        try:
            message = MIMEMultipart()
            message['From'] = email_contact.from_email or self.username
            message['To'] = email_contact.to_email
            message['Subject'] = email_contact.subject

            html_body = f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                            padding: 20px;
                            background-color: #f4f4f9;
                        }}
                        h1 {{
                            color: #333;
                        }}
                        p {{
                            font-size: 16px;
                            color: #555;
                        }}
                        .important {{
                            color: red;
                            font-weight: bold;
                        }}
                    </style>
                </head>
                <body>
                    <h1>{email_contact.subject}</h1>
                    <p>{email_contact.body}</p>
                    <p class="important">Este es un mensaje importante con formato HTML y estilos.</p>
                </body>
                </html>
                """

            message.attach(MIMEText(html_body, 'html'))

            # message.attach(MIMEText(body, 'html'))

            # if attachments:
            #     for file_path in attachments:
            #         try:
            #             with open(file_path, 'rb') as attachment:
            #                 part = MIMEBase('application', 'octet-stream')
            #                 part.set_payload(attachment.read())
            #                 encoders.encode_base64(part)
            #                 part.add_header(
            #                     'Content-Disposition',
            #                     f'attachment; filename={file_path.split("/")[-1]}',
            #                 )
            #                 message.attach(part)
            #         except FileNotFoundError:
            #             print(f"El archivo {file_path} no se encuentra.")

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