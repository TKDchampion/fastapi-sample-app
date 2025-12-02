from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.permission_entity import PermissionEntity


def get_permissions(db: Session):
    return db.execute(select(PermissionEntity.key, PermissionEntity.type)).all()
