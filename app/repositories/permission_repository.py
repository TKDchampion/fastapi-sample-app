from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity


def get_permissions(db: Session):
    return db.execute(select(PermissionEntity.key, PermissionEntity.type)).all()


def get_all_permissions_org(db: Session):
    return (
        db.execute(
            select(
                PermissionEntity.id, PermissionEntity.key, PermissionEntity.name
            ).where(PermissionEntity.type == "org")
        )
        .mappings()
        .all()
    )


def get_roles_with_permissions(db: Session, org_id: int):
    return db.scalars(
        select(RoleEntity)
        .where(RoleEntity.organization_id == org_id)
        .options(selectinload(RoleEntity.permissions))
    ).all()
