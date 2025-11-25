from sqlalchemy import insert, select
from sqlalchemy.orm import Session
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
