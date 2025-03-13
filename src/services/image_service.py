from io import BytesIO
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
        try:
            file_size = len(image_file.file.read())
            image_file.file.seek(0)  

            if file_size > self.MAX_FILE_SIZE:
                raise JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen no puede exceder los 2MB")

            file_extension = self.mime_to_extension[image_file.content_type]
            filename = await self.reset_name_image(f"{uuid.uuid4().hex}{file_extension}")
            file_location = os.path.join(self.path_image, filename)

            image = Image.open(image_file.file)
            
            image.save(file_location, optimize=True, quality=85)
            
            while os.path.getsize(file_location) > 512 * 1024:
                # quality = image.info.get('quality', 85)  # Usa 85 si no se encuentra 'quality'
                quality = image.encoderconfig[0]
                new_quality = quality - 5 if quality > 5 else 5
                image.save(file_location, optimize=True, quality=new_quality)
                # image.save(file_location, optimize=True, quality=image.info['quality'] - 5)

            return filename
        except Exception as e:
            return None
        

    # async def save_image(self, image_file: UploadFile) -> str | None:
    #     if 'image' not in image_file.content_type:
    #         raise JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no soportado. Los formatos válidos son: JPEG, PNG")
        
    #     # Asegúrate de reposicionar el puntero del archivo al principio
    #     image_file.file.seek(0)
        
    #     # Leer el archivo de manera asíncrona
    #     image_data = await image_file.read()

    #     # Verificar si se obtuvo un archivo vacío
    #     if not image_data:
    #         raise JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo está vacío o no se pudo leer correctamente.")

    #     # Convertir los datos leídos en BytesIO
    #     image_bytes = BytesIO(image_data)

    #     # Verificar el tamaño del archivo
    #     file_size = len(image_data)
    #     if file_size > self.MAX_FILE_SIZE:
    #         raise JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen no puede exceder los 2MB")

    #     # Obtener la extensión del archivo
    #     file_extension = self.mime_to_extension[image_file.content_type]
    #     filename = await self.reset_name_image(f"{uuid.uuid4().hex}{file_extension}")
    #     file_location = os.path.join(self.path_image, filename)

    #     try:
    #         # Abrir la imagen desde BytesIO
    #         image = Image.open(image_bytes)
    #         image.save(file_location, optimize=True, quality=85)

    #         # Reducir el tamaño de la imagen si es necesario
    #         while os.path.getsize(file_location) > 512 * 1024:
    #             # Verificar si 'quality' existe en image.info antes de intentar restarlo
    #             quality = image.info.get('quality', 85)  # Usa 85 si no se encuentra 'quality'
    #             new_quality = quality - 5 if quality > 5 else 5
    #             image.save(file_location, optimize=True, quality=new_quality)

    #         return filename
    #     except Exception as e:
    #         return None

    # async def save_image(self, image_file: UploadFile) -> str | None:
    #     if 'image' not in image_file.content_type:
    #         raise JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no soportado. Los formatos válidos son: JPEG, PNG")
        
    #     image_file.file.seek(0)
    #     image = Image.open(image_file.file)

    #     image_data = await image_file.read()

    #     if not image_data:
    #         raise JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo está vacío o no se pudo leer correctamente.")

    #     image_bytes = BytesIO(image_data)

    #     file_size = len(image_data)
    #     if file_size > self.MAX_FILE_SIZE:
    #         raise JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen no puede exceder los 2MB")

    #     file_extension = self.mime_to_extension[image_file.content_type]
    #     filename = await self.reset_name_image(f"{uuid.uuid4().hex}{file_extension}")
    #     file_location = os.path.join(self.path_image, filename)

    #     print(f"Tipo de image_bytes antes de Image.open(): {type(image_bytes)}")
    #     print(f"Contenido de image_bytes (primeros 50 bytes): {image_bytes.getvalue()[:50]}")
    #     print(f"Tamaño de image_bytes: {len(image_bytes.getvalue())}")

    #     if not isinstance(image_bytes, BytesIO):
    #         print(f"Error: image_bytes no es un BytesIO, sino {type(image_bytes)}")
    #         return None
        
    #     try:
    #         image = Image.open(fp= image_bytes, mode='r') # AQUI OCURRE EL ERROR
    #         image.save(file_location, optimize=True, quality=85)

    #         while os.path.getsize(file_location) > 512 * 1024:
    #             quality = image.info.get('quality', 85)
    #             new_quality = quality - 5 if quality > 5 else 5
    #             image.save(file_location, optimize=True, quality=new_quality)

    #         return filename
    #     except Exception as e:
    #         print(f"Error al procesar la imagen: {e}")
    #         return None
            
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