import logging, os
from decouple import config
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from datetime import date
from sqlmodel import select
from src.database.db import db
from src.models.appointment import Appointment, StateAppointment
from src.models.blog_model import Blog

async def drive_backup_images():
    try:
        SERVICE_ACCOUNT_FILE = r'./credentials.json'
        SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file']

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        drive_service = build('drive', 'v3', credentials=credentials)

        folder_id = config('ID_FOLDER_IMAGES')

        query = f"'{folder_id}' in parents and (mimeType='image/jpeg' or mimeType='image/png')"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        folder_path = os.path.join('src','images','blog') 
        os.makedirs(folder_path, exist_ok=True)
        image_extensions = ['.jpg', '.jpeg', '.png']

        list_images = []

        try:
            images = [file for file in os.listdir(folder_path) 
                    if os.path.splitext(file)[1].lower() in image_extensions]
            
            if images:
                print("Imágenes encontradas:")
                for image in images:
                    list_images.append(image)
            else:
                print("No se encontraron imágenes en la carpeta especificada.")
        except Exception as e:
            logging.error(f"Error al listar las imágenes: {e}")

        list_name_images_drive = [file['name'] for file in files]

        for elem in list_images:
            if elem not in list_name_images_drive:
                file_extension = elem.split('.')[-1].lower()
                mime_type = ''
                
                if file_extension == 'png':
                    mime_type = 'image/png'
                elif file_extension == 'jpg' or file_extension == 'jpeg':
                    mime_type = 'image/jpeg'
                else:
                    raise ValueError("Formato de imagen no soportado.")

                file_metadata = {'name': elem, 'parents': [config('ID_FOLDER_IMAGES')]}
                media = MediaFileUpload(os.path.join(folder_path, elem), mimetype=mime_type)

                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                logging.info(f"Imagen cargada con éxito. ID: {file.get('id')}")
    except Exception as e:
        logging.error(f"Error al realizar el backup de las imagenes: {e}")
