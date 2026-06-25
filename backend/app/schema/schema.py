from pydantic import BaseModel, EmailStr

from app.models.models import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    role: UserRole
    remember_me: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserJWT(BaseModel):
    sub: str
    role: UserRole
