import logging
import uuid, os
from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
import cv2
import numpy as np


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
            raise JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de imagen no soportado. Los formatos válidos son: JPEG, PNG"
            )
        try:
            logging.info("Guardando imagen")

            file_size = len(image_file.file.read())
            image_file.file.seek(0)

            if file_size > self.MAX_FILE_SIZE:
                raise JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="La imagen no puede exceder los 2MB"
                )

            file_extension = self.mime_to_extension[image_file.content_type]
            filename = await self.reset_name_image(f"{uuid.uuid4().hex}{file_extension}")
            file_location = os.path.join(self.path_image, filename)

            image_data = await image_file.read()
            print(f"Tipo de image_data: {type(image_data)}, Tamaño: {len(image_data)} bytes")

            image_array = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if image is None:
                raise JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo no es una imagen válida"
                )

            image_resized = await self.resize_image(image)

            if file_extension == '.jpg':
                cv2.imwrite(file_location, image_resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            elif file_extension == '.png':
                cv2.imwrite(file_location, image_resized, [cv2.IMWRITE_PNG_COMPRESSION, 9])

            while os.path.getsize(file_location) > 512 * 1024: 
                if file_extension == '.jpg':
                    quality = max(5, 85 - 5) 
                    cv2.imwrite(file_location, image_resized, [cv2.IMWRITE_JPEG_QUALITY, quality])
                elif file_extension == '.png':
                    compression = max(3, 9 - 1)  
                    cv2.imwrite(file_location, image_resized, [cv2.IMWRITE_PNG_COMPRESSION, compression])

            logging.info("Imagen guardada")
            return filename
        except Exception as e:
            logging.error(f"Error al guardar imagen: {e}")
            return None

    async def resize_image(self, image: np.ndarray) -> np.ndarray:
        max_dimension = 1024
        h, w = image.shape[:2]
        if max(h, w) > max_dimension:
            scaling_factor = max_dimension / float(max(h, w))
            new_h, new_w = int(h * scaling_factor), int(w * scaling_factor)
            image_resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return image_resized
        return image
    
    async def delete_image(self, filename: str) -> None:
        try:
            media_path = os.path.join(self.path_image, filename)
            if os.path.exists(media_path):
                os.remove(media_path)
            else:
                logging.info("Imagen no encontrada, para eliminar")
        except Exception as e:
            logging.error(f"Error al eliminar imagen: {e}")
            
        
    async def get_image(self, file_name: str):
        try:
            logging.info("Obteniendo imagen")
            file_path = os.path.join(self.path_image, file_name)

            if not os.path.exists(file_path):
                return JSONResponse(status_code=404, content={"detail": "Imagen no encontrada"})

            file_extension = os.path.splitext(file_name)[1].lower()
            mime_type = self.mime_to_extension.get(file_extension, "application/octet-stream")

            logging.info("Imagen obtenida")

            return FileResponse(file_path, media_type=mime_type, filename=file_name, status_code= status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"Error al obtener imagen: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener la imagen"
            )