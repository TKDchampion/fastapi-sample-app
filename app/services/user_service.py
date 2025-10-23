from sqlalchemy.orm import Session
from app.repositories import user_repository
from app.dtos.user_dto import UserCreateDTO


def get_users(db: Session):
    return user_repository.get_all_users(db)


def add_user(db: Session, user: UserCreateDTO):
    return user_repository.create_user(db, user)


def get_user_by_email(db: Session, email: str):
    return user_repository.get_user_by_email(db, email)
