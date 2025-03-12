from datetime import date
import re
import bcrypt
from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str
    first_name: str
    last_name: str

    @classmethod
    def hash_password(cls, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @field_validator('username')
    def username_validator(cls, username):
        if len(username) < 3 or len(username) > 20:
            raise ValueError('El username debe contener entre 3 y 20 caracteres')
        if ' ' in username:
            raise ValueError('El username no puede contener espacios')
        return username
    
    @field_validator('password_hash')
    def password_validator(cls, password_hash):
        if len(password_hash) < 8:
            raise ValueError('El password debe contener al menos 8 caracteres')
        if not re.search(r'[A-Z]', password_hash):
            raise ValueError('El password debe contener al menos una mayuscula')
        if not re.search(r'\d', password_hash):
            raise ValueError('El password debe contener al un numero')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password_hash):
            raise ValueError('El password debe contener al menos un caracter especial')
        return cls.hash_password(password_hash)
    
    @field_validator('email')
    def email_validator(cls, email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError('El correo electrónico no es válido')
        return email
    