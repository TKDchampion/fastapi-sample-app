from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import user_service
from app.dtos.user_dto import UserCreate, UserRead
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    return user_service.get_users(db)


@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.add_user(db, user)
