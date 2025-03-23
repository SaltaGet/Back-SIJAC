from functools import wraps
from typing import Callable, List
from fastapi import HTTPException, status
from src.models.user_model import User

def authorization(roles: List[str]):
    """
    Decorador para proteger rutas basadas en el rol del usuario.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args, 
            user: User,
            **kwargs
        ):
            if user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para acceder a este recurso",
                )

            return await func(*args, **kwargs, user=user) 
        return wrapper
    return decorator
