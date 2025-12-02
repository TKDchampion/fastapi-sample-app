from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, selectinload
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.associations_entity import (
    role_permissions as role_permissions_table,
)


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


def delete_role_permissions(db: Session, role_id: int):
    """Delete all permissions for a specific role."""
    db.execute(
        delete(role_permissions_table).where(
            role_permissions_table.c.role_id == role_id
        )
    )


def add_role_permissions(db: Session, role_id: int, permission_ids: list[int]):
    """Insert a new list of permissions for a role."""
    if not permission_ids:
        return

    db.execute(
        insert(role_permissions_table),
        [{"role_id": role_id, "permission_id": pid} for pid in permission_ids],
    )
