from datetime import date, timedelta
import logging
import os
import bcrypt
from fastapi import HTTPException, Request, UploadFile, status
from src.config.timezone import get_timezone
from src.models.refresh_token import HistorialRefreshToken
from src.models.user_model import RoleUser, User
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.user_schema.user_create import UserCreate
from src.schemas.user_schema.user_credentials import UserCredentials
from src.schemas.user_schema.user_response import UserResponse
from src.schemas.user_schema.user_update import UserUpdate
from src.services.auth_service import AuthService
from src.services.image_service import ImageTool

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def login(self, credentials:UserCredentials):
        try:
            logging.info("Logueando usuario")
            statement = select(User).where(User.email == credentials.email)
            user: User | None = (await self.session.exec(statement)).first()

            if user is None:
                return JSONResponse(
                    content={"detail": "Credenciales incorrectas"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            if self.verify_password(credentials.password, user.password_hash) == False:
                return JSONResponse(
                    content={"detail": "Credenciales incorrectas"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            token = await AuthService().get_token(user)

            sttmt_rt = token.copy()
            sttmt_rt['user_id'] = user.id
            sttmt_rt['expire'] = get_timezone() + timedelta(days=7)

            self.session.add(HistorialRefreshToken(**sttmt_rt))

            await self.session.commit()

            logging.info("Login exitoso")

            return JSONResponse(
                content=token,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            logging.error("Error login: {e}")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar loguear")
        
    async def logout(self, user, token, refresh_token):
        try:
            statement = select(HistorialRefreshToken).where(
                HistorialRefreshToken.user_id == user.user.id,
                HistorialRefreshToken.refresh_token == refresh_token,
                HistorialRefreshToken.token == token
                )
            token: HistorialRefreshToken | None = (await self.session.exec(statement)).first()

            if token is None:
                return JSONResponse(
                    content={"detail": "Credenciales incorrectas"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            await self.session.delete(token)
            await self.session.commit()

            return JSONResponse(
                content={"detail": "Logout exitoso"},
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar logout")

    
    async def create_user(self, user: UserCreate, image: UploadFile, is_admin: bool = False):
            try:
                logging.info("Creando usuario")
                statement= select(User).where(User.email == user.email)
                                            
                result = await self.session.exec(statement)
                user_exist: User | None = result.first()
                
                if(user_exist != None):
                    if user_exist.username == user.username:
                        return JSONResponse(
                            status_code=status.HTTP_409_CONFLICT, 
                            content={"detail": "El username ya se encuentra en uso"}
                            )
                    if user_exist.email == user.email:
                        return JSONResponse(
                            status_code=status.HTTP_409_CONFLICT, 
                            content={"detail": "El email ya existe."}
                            )
                 
                new_image = await ImageTool(os.path.join('src', 'images', 'user')).save_image(image)

                if new_image is None:
                    return JSONResponse(
                        content={
                            "detail": "Error al guardar la imagen"
                            },
                        status_code=status.HTTP_424_FAILED_DEPENDENCY
                    )
            
                new_user: User = User(**user.model_dump(), url_image= new_image)

                if is_admin == True:
                    new_user.role = RoleUser.ADMIN

                self.session.add(new_user)

                await self.session.commit()
                logging.info("usuario creado")

                return JSONResponse(
                            status_code=status.HTTP_201_CREATED, 
                            content={"detail": "Usuario creado exitosamente."}
                            )
            except Exception as e:
                logging.error(f"Error al crear usuario: {e}")
                if new_image:
                    ImageTool(os.path.join('src', 'images', 'user')).delete_image(new_image)
                await self.session.rollback()
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al crear usuario.')
            
    async def update_user(self, user_update: UserUpdate, user: User, image: UploadFile | None):
            try:
                user_exist: User | None = await self.session.get(User, user.id)
                
                if(user_exist == None):
                    return JSONResponse(
                            status_code=status.HTTP_404_NOT_FOUND, 
                            content={"detail": "Usuario no encontrado"}
                            )

                user_exist.username = user_update.username 
                user_exist.first_name = user_update.first_name 
                user_exist.last_name = user_update.last_name
                user_exist.specialty = user_update.specialty

                if image is not None:
                    image_tool = ImageTool(os.path.join('src', 'images', 'user'))
                    file_name = await image_tool.save_image(image)

                    if file_name is None:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al intentar editar el usuario"
                        )
                    
                    await image_tool.delete_image(user_exist.url_image)

                    user_exist.url_image = file_name

                await self.session.commit()

                return JSONResponse(
                            status_code=status.HTTP_201_CREATED, 
                            content={"detail": "Usuario editado exitosamente."}
                            )
            except Exception as e:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al editar usuario.')
            
    async def get_users(self, request: Request):
        try:
            logging.info("Obteniendo usuarios")
            statement = select(User).where(User.role == RoleUser.USER)
            users = await self.session.exec(statement)
            users = users.all()

            scheme = request.scope.get("scheme") 
            host = request.headers.get("host")   
            full_url = f"{scheme}://{host}/image/get_image_user/"

            users_list = []
            for user in users:
                user.url_image = full_url + user.url_image
                u = UserResponse.model_validate(user).model_dump(mode='json')
                users_list.append(u)

            return JSONResponse(
                status_code=status.HTTP_200_OK, 
                content=users_list
            )
        except Exception as e:
            logging.error(f"Error al obteniendo usuarios: {e}")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al obtener usuarios.')
            
    async def refresh_token(self, user: User, token: str, refresh_token: str):
        try:
            statement = select(HistorialRefreshToken).where(
                HistorialRefreshToken.user_id == user.id,
                HistorialRefreshToken.refresh_token == refresh_token,
                HistorialRefreshToken.token == token
            )
            historial_rt: HistorialRefreshToken | None = (await self.session.exec(statement)).first()

            if not historial_rt:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    content={'detail':'Credenciales no encontradas'}
                )

            rt_decode = await AuthService().decode_token(refresh_token)

            if rt_decode == False:
                await self.session.delete(historial_rt)
                await self.session.commit()

                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    content={'detail':'Refresh token expirado.'}
                )

            new_token = await AuthService().create_token(user)
            new_refresh_token = await AuthService().create_refresh_token(user)

            historial_rt.token = new_token
            historial_rt.refresh_token = new_refresh_token

            await self.session.commit()

            return {"token": new_token, "refresh_token": new_refresh_token}

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al actualizar el token.')


    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def me(self, user: User):
        user_dict = user.model_dump()
        for key, value in user_dict.items():
            if isinstance(value, date):
                user_dict[key] = value.isoformat()

        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content=user_dict
        )
    
    async def validate_email(self, email: str):
        statement = select(User).where(User.email == email)
        exist = await self.session.exec(statement)
        user: User | None = exist.first()
        return user is None 
    
    
