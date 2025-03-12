import uuid, os
from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image


class ImageTool:
    MAX_FILE_SIZE = 2 * 1024 * 1024  #2 MB
    ALLOWED_MIME_TYPES = [
        "image/jpeg",
        "image/png",
    ]
    mime_to_extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
    }

    def __init__(self, path_image: str) -> None:
        self.path_image = path_image
        os.makedirs(self.path_image, exist_ok=True)

    async def reset_name_image(self, filename: str) -> str:
        name, extension = os.path.splitext(filename)
        new_name = f"{uuid.uuid4()}{extension}"
        return new_name
    
    async def save_image(self, image_file: UploadFile) -> str | None:
        if 'image' not in image_file.content_type:
            raise JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no soportado. Los formatos válidos son: JPEG, PNG")
        file_size = len(image_file.file.read())
        image_file.file.seek(0)  # Reset the file pointer to the beginning after reading size

        if file_size > self.MAX_FILE_SIZE:
            raise JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen no puede exceder los 2MB")

        file_extension = self.mime_to_extension[image_file.content_type]
        filename = self.reset_name_image(f"{uuid.uuid4().hex}{file_extension}")
        file_location = os.path.join(self.path_image, filename)

        try:
            image = Image.open(image_file.file)
            
            while os.path.getsize(file_location) > 512 * 1024:
                image.save(file_location, optimize=True, quality=image.info['quality'] - 5)

            return filename
        except Exception as e:
            return None
        
    async def delete_image(self, filename: str) -> None:
        media_path = os.path.join(self.path_image, filename)
        if os.path.exists(media_path):
            os.remove(media_path)
        else:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
    async def get_image(self, file_name: str):
        try:
            file_path = os.path.join(self.path_image, file_name)

            if not os.path.exists(file_path):
                return JSONResponse(status_code=404, content={"detail": "Imagen no encontrada"})

            file_extension = os.path.splitext(file_name)[1].lower()
            mime_type = self.mime_to_extension.get(file_extension, "application/octet-stream")

            return FileResponse(file_path, media_type=mime_type, filename=file_name, status_code= status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener la imagen"
            )