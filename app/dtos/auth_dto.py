from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl


class GoogleAuthCodeDTO(BaseModel):
    code: str
    redirect_uri: HttpUrl


class AuthLoginResponseDTO(BaseModel):
    sub: str
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[HttpUrl] = None
    email: EmailStr
    email_verified: bool
    hd: Optional[str] = None
    token: str
