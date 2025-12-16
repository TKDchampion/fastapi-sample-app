from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session, joinedload
from app.entities.organization_entity import OrganizationEntity
from app.entities.role_entity import RoleEntity
from app.entities.associations_entity import (
    user_roles as user_roles_table,
)


def create_roles(db: Session, org: OrganizationEntity):
    default_roles = [
        RoleEntity(
            organization_id=org.id,
            name="admin",
            description="Organization administrator with full access",
        ),
        RoleEntity(
            organization_id=org.id,
            name="manager",
            description="Organization manager with management permissions",
        ),
        RoleEntity(
            organization_id=org.id,
            name="member",
            description="Standard member with basic access",
        ),
    ]

    db.add_all(default_roles)


def role_belongs_to_org(db: Session, role_id: int, org_id: int) -> bool:
    stmt = select(RoleEntity.id).where(
        RoleEntity.id == role_id, RoleEntity.organization_id == org_id
    )
    result = db.execute(stmt).scalar_one_or_none()
    return result is not None


def create_user_role(db: Session, org_id: int, role_id: int, user_id: int):
    stmt = (
        insert(user_roles_table)
        .values(
            user_id=user_id,
            scope_type="org",
            scope_id=org_id,
            role_id=role_id,
        )
        .returning(user_roles_table)
    )

    result = db.execute(stmt)
    return result.fetchone()


def roles_by_org(db: Session, org_id: int) -> bool:
    stmt = select(RoleEntity.id, RoleEntity.name).where(
        RoleEntity.organization_id == org_id
    )
    return db.execute(stmt).mappings().all()


def update_user_role(db: Session, user_id: int, org_id: int, role_id: int):
    stmt = (
        update(user_roles_table)
        .where(
            user_roles_table.c.user_id == user_id,
            user_roles_table.c.scope_type == "org",
            user_roles_table.c.scope_id == org_id,
        )
        .values(role_id=role_id)
        .returning(user_roles_table)
    )

    result = db.execute(stmt)
    return result.fetchone()


def get_user_role(db: Session, user_id: int, org_id: int):
    stmt = select(user_roles_table).where(
        user_roles_table.c.user_id == user_id,
        user_roles_table.c.scope_type == "org",
        user_roles_table.c.scope_id == org_id,
    )
    return db.execute(stmt).fetchone()


def delete_user_role(db: Session, user_id: int, org_id: int):
    stmt = (
        delete(user_roles_table)
        .where(
            user_roles_table.c.user_id == user_id,
            user_roles_table.c.scope_type == "org",
            user_roles_table.c.scope_id == org_id,
        )
        .returning(user_roles_table.c.user_id)
    )

    result = db.execute(stmt)
    row = result.fetchone()

    return row[0] if row else None


def get_role_with_permissions(db: Session, role_id: int):
    """Get role with its permissions eagerly loaded"""
    stmt = (
        select(RoleEntity)
        .where(RoleEntity.id == role_id)
        .options(joinedload(RoleEntity.permissions))
    )
    return db.execute(stmt).scalar_one_or_none()
