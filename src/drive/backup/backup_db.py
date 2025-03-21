import logging
from decouple import config
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from datetime import date


async def drive_backup_db():
  try:
    SERVICE_ACCOUNT_FILE = r'./credentials.json'

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    drive_service = build('drive', 'v3', credentials=credentials)

    file_metadata = {'name': f'sijac-{date.today().isoformat()}.db', 'parents': [config('ID_FOLDER')]}
    media = MediaFileUpload(r'./sijac.db', mimetype='application/octet-stream')

    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    logging.info(f"Backup realizado con éxito. ID: {file.get('id')}")
  except Exception as e:
    logging.error(f"Error al realizar el backup: {e}")
