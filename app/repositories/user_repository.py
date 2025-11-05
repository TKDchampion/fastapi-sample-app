from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.organization_entity import OrganizationEntity
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.si_entity import SIEntity
from app.entities.user_entity import UserEntity
from app.dtos.user_dto import UserCreateDTO
from app.entities.associations_entity import (
    user_roles as user_roles_table,
)


def get_all_users(db: Session):
    return db.query(UserEntity).all()


def create_user(db: Session, user: UserCreateDTO):
    db_user = UserEntity(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(UserEntity).filter(UserEntity.email == email).first()


def get_user(db: Session, user_id: int):
    return db.scalar(select(UserEntity).where(UserEntity.id == user_id))


def get_user_roles(db: Session, user_id: int):
    return db.execute(
        select(
            user_roles_table.c.scope_type,
            user_roles_table.c.scope_id,
            user_roles_table.c.role_id,
            user_roles_table.c.isActive,
            SIEntity.id.label("si_id"),
            SIEntity.name.label("si_name"),
            OrganizationEntity.id.label("org_id"),
            OrganizationEntity.name.label("org_name"),
            RoleEntity.name.label("role_name"),
            PermissionEntity.name.label("perm_name"),
            PermissionEntity.type.label("perm_type"),
        )
        .join(RoleEntity, RoleEntity.id == user_roles_table.c.role_id)
        .join(RoleEntity.permissions)
        .outerjoin(SIEntity, SIEntity.id == user_roles_table.c.scope_id)
        .outerjoin(
            OrganizationEntity, OrganizationEntity.id == user_roles_table.c.scope_id
        )
        .where(user_roles_table.c.user_id == user_id)
    ).all()


def get_permissions(db: Session):
    return db.execute(select(PermissionEntity.name, PermissionEntity.type)).all()


def get_all_orgs(db: Session):
    return db.execute(
        select(OrganizationEntity.id, OrganizationEntity.name, OrganizationEntity.si_id)
    ).all()


def get_si_org_tree(db: Session):
    stmt = (
        select(
            SIEntity.id, SIEntity.name, OrganizationEntity.id, OrganizationEntity.name
        )
        .join(OrganizationEntity, OrganizationEntity.si_id == SIEntity.id, isouter=True)
        .order_by(SIEntity.id)
    )
    return db.execute(stmt).all()
