from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import user_service
from app.dtos.user_dto import UserCreateDTO, UserReadDTO
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserReadDTO])
def get_users(db: Session = Depends(get_db)):
    return user_service.get_users(db)


@router.post("", response_model=UserReadDTO)
def create_user(user: UserCreateDTO, db: Session = Depends(get_db)):
    return user_service.add_user(db, user)
