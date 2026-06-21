from pydantic import BaseModel, EmailStr

from app.models.models import UserRole


class UserCreate(BaseModel):
    fullname: str
    password: str
    email: EmailStr
    role: UserRole
    remember_me: bool = False
