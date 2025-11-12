from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.organization_entity import OrganizationEntity
from app.entities.role_entity import RoleEntity


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
