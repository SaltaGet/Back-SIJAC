from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    specialty: str
    url_image: str

    class Config:
        from_attributes = True