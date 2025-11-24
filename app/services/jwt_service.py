# app/services/jwt_service.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.database import get_db
from app.dtos.user_dto import UserReadDTO
from app.services import user_service


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
security = HTTPBearer()

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Please configure it via .env or environment variable."
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = (
            payload.get("member", {}).get("email")
            or payload.get("email")
            or payload.get("sub")
        )
        if not email:
            raise HTTPException(
                status_code=401,
                detail={"msg": "Token invalid", "type": "token_invalid"},
            )

        user = user_service.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=401,
                detail={"msg": "User not found", "type": "token_invalid"},
            )

        return UserReadDTO(
            id=user.id, name=user.name, email=user.email, picture=user.picture
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"msg": "Token expired", "type": "token_expired"},
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"msg": "Token invalid", "type": "token_invalid"},
        )


def token_required(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"msg": "Token missing", "type": "token_missing"},
        )
    token = auth_header.split(" ")[1]
    return decode_access_token(token, db)
