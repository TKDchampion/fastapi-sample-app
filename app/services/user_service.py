from sqlalchemy.orm import Session
from app.repositories import user_repository
from app.dtos.user_dto import UserCreate


def get_users(db: Session):
    return user_repository.get_all_users(db)


def add_user(db: Session, user: UserCreate):
    return user_repository.create_user(db, user)
