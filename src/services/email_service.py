import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

from src.models.appointment import Appointment, StateAppointment
from src.schemas.user_schema.email_contact import EmailContact

class EmailService:
    def __init__(self):
        self.smtp_server = config('SMTP_SERVER')
        self.port = config('EMAIL_PORT')
        self.email = config('EMAIL')
        self.password = config('EMAIL_PASSWORD')

    async def send_email(self, subject: str, to_email:str, html_message: str):
        logging.info("Enviando email")
        message = MIMEMultipart()
        message['From'] = self.email
        message['To'] = to_email
        message['Subject'] = subject

        message.attach(MIMEText(html_message, 'html'))

        with smtplib.SMTP(self.smtp_server, self.port) as server:
            try:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(message)
                logging.info("Email enviado")
            except smtplib.SMTPException as e:
                logging.error(f"Error sending email: {e}")

    async def send_email_client(self, state: StateAppointment, appointment: Appointment):  
        try:
            if state == StateAppointment.NULL:
                html = f"""
                    <html>
                    <head>
                    </head>
                    <body style="padding: 40px;">
                        <h2 style="text-align: center;">Hola {appointment.full_name}!!!</h2>
                        <p style="text-align: start;">Usted ha solicitado un turno</p>
                        <p>dia: {appointment.date_get.strftime('%d-%m-%Y')}</p>
                        <p>Inicio: {appointment.start_time.strftime('%H-%M')}</p>
                        <p>Inicio: {appointment.end_time.strftime('%H-%M')}</p>
                        <p>Por el siguiente motivo:</p>
                        <p style="text-align: center; margin: 20px 40px 20px 40px; font-style: italic;">"{appointment.reason}"</p>
                        <p style="text-align: center;">A partir del mensaje recibido tiene 30 minutos para confirmar la solicitud del turno</p>
                        <a href="https://www.facebook.com" target="_blank">
                            <button>Confirmar solicitud</button>
                        </a>
                        <h2 style="text-align: center;">Gracias por contacarte con SIJAC!!!</h2>
                    </body>
                    </html>
                """

            if state == StateAppointment.ACCEPT:
                html = f"""
                    <html>
                    <head>
                    </head>
                    <body style="padding: 40px;">
                        <h2 style="text-align: center;">Hola {appointment.full_name}!!!</h2>
                        <p style="text-align: start;">Su turno ha sifo confimado, tenga en cuenta los datos de su turno.</p>
                        <p>dia: {appointment.date_get.strftime('%d-%m-%Y')}</p>
                        <p>Inicio: {appointment.start_time.strftime('%H-%M')}</p>
                        <p>Inicio: {appointment.end_time.strftime('%H-%M')}</p>
                        <p>Por el siguiente motivo:</p>
                        <p style="text-align: center; margin: 20px 40px 20px 40px; font-style: italic;">"{appointment.reason}"</p>
                        <p style="text-align: center;">Lo esperamos</p>
                        <h2 style="text-align: center;">Gracias por contacarte con SIJAC!!!</h2>
                    </body>
                    </html>
                """

            if state == StateAppointment.CANCEL:
                html = f"""
                    <html>
                    <head>
                    </head>
                    <body style="padding: 40px;">
                        <h2 style="text-align: center;">Hola {appointment.full_name}!!!</h2>
                        <p style="text-align: start;">Su turno a sido cancelado</p>
                        <p style="text-align: start;">Datos del turno cancelado:</p>
                        <p>dia: {appointment.date_get.strftime('%d-%m-%Y')}</p>
                        <p>Inicio: {appointment.start_time.strftime('%H-%M')}</p>
                        <p>Inicio: {appointment.end_time.strftime('%H-%M')}</p>
                        <p>Por el siguiente motivo:</p>
                        <p style="text-align: center; margin: 20px 40px 20px 40px; font-style: italic;">"{appointment.reason}"</p>
                        <p style="text-align: center;">Para confirmar la solicitud del turno es necesario hacer click en el siguiente botón</p>
                        <a href="https://www.facebook.com" target="_blank">
                            <button>Confirmar solicitud</button>
                        </a>
                        <h2 style="text-align: center;">Gracias por contacarte con SIJAC!!!</h2>
                    </body>
                    </html>
                """

            if state == StateAppointment.REJECT:
                html = f"""
                    <html>
                    <head>
                    </head>
                    <body style="padding: 40px;">
                        <h2 style="text-align: center;">Hola {appointment.full_name}!!!</h2>
                        <p style="text-align: start;">Lamentablemente tenemos que informarle que el su turno ha sido cancelado, por el siguiente motivo</p>
                        <p style="text-align: start;">Le solicitamos solicitar un nuevo turno desde nuestra web o acercarce por nuestras oficinas</p>
                        <p style="text-align: start;">Datos del turno:</p>
                        <p>dia: {appointment.date_get.strftime('%d-%m-%Y')}</p>
                        <p>Inicio: {appointment.start_time.strftime('%H-%M')}</p>
                        <p>Inicio: {appointment.end_time.strftime('%H-%M')}</p>
                        <p>Por el siguiente motivo:</p>
                        <p style="text-align: center; margin: 20px 40px 20px 40px; font-style: italic;">"{appointment.reason}"</p>
                        <h2 style="text-align: center;">Gracias por contacarte con SIJAC!!!</h2>
                    </body>
                    </html>
                """

            await self.send_email(subject='Turno SIJAC', to_email=appointment.email, html_message=html)
            
            return True
        except Exception as e:
            logging.error(f"Error al enviar email")
            return False

    async def send_email_lawyer(self, appointment: Appointment):   
        try:
            html = f"""
                <html>
                <head>
                </head>
                <body style="padding: 40px;">
                    <h2>Tiene un nuevo turno a confirmar</h2>
                    <h2>Datos de Contacto</h2>
                    <p style="text-indent: 40px;"><strong>Nombre: </strong>{appointment.full_name}</p>
                    <p style="text-indent: 40px;"><strong>Teléfono: </strong>{appointment.cellphone}</p>
                    <p style="text-indent: 40px;"><strong>Email: </strong> {appointment.email}</p>

                    <h3>Motivo:</h3>
                    <p style="text-indent: 40px;">{appointment.reason}</p>
                </body>
                </html>
            """

            await self.send_email(subject='Nuevo turno SIJAC', to_email='danielmchachagua@gmail.com', html_message=html)

            return True
        except Exception as e:
            logging.error(f"Error al enviar email")
            return False 
