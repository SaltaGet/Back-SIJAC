from pydantic import BaseModel, field_validator

class UpdatePassword(BaseModel):
  old_password: str
  new_password: str
  repeat_new_password: str

  @field_validator('new_password')
  def password_validator(cls, new_password):
    if len(new_password) < 8:
        raise ValueError('El password debe contener al menos 8 caracteres')
    return new_password