from datetime import date
import uuid
from sqlmodel import Field, SQLModel, Relationship

class RoomImage(SQLModel, table= True):
    __tablename__ = "room_images"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    url_image: str = Field()
    room_id: str = Field(foreign_key= 'rooms.id', index= True, ondelete= 'CASCADE')
    room: "Room" = Relationship(back_populates="room_images")