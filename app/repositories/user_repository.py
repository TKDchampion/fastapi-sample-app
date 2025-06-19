from sqlalchemy.orm import Session
from app.entities.user_entity import UserEntity
from app.dtos.user_dto import UserCreate


def get_all_users(db: Session):
    return db.query(UserEntity).all()


def create_user(db: Session, user: UserCreate):
    db_user = UserEntity(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
