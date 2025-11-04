from collections import defaultdict
from sqlalchemy import select
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from app.entities.organization_entity import OrganizationEntity
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.si_entity import SIEntity
from app.entities.user_entity import UserEntity
from app.dtos.user_dto import RoleRow, UserCreateDTO
from app.entities.associations_entity import (
    user_roles as user_roles_table,
    role_permissions as role_permissions_table,
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


def fetch_user(db: Session, user_id: int) -> Optional[UserEntity]:
    return db.scalar(select(UserEntity).where(UserEntity.id == user_id))


def fetch_all_permissions(db: Session) -> List[str]:
    # Names only; keep order deterministic
    rows = db.execute(
        select(PermissionEntity.name)
        .where(PermissionEntity.name.is_not(None))
        .order_by(PermissionEntity.name.asc())
    ).all()
    return [r[0] for r in rows]


def fetch_user_roles_joined(db: Session, user_id: int) -> List[RoleRow]:
    """
    Single batched query:
    user_roles (scope_type, scope_id, isActiveOrg, role_id, role_name) +
    left-join role->permissions (permission_name)
    """
    # user_roles -> RoleEntity
    base = (
        select(
            user_roles_table.c.scope_type,
            user_roles_table.c.scope_id,
            user_roles_table.c.isActiveOrg,
            RoleEntity.id.label("role_id"),
            RoleEntity.name.label("role_name"),
            PermissionEntity.name.label("permission_name"),
        )
        .join(RoleEntity, RoleEntity.id == user_roles_table.c.role_id)
        .join(
            role_permissions_table,
            role_permissions_table.c.role_id == RoleEntity.id,
            isouter=True,
        )
        .join(
            PermissionEntity,
            PermissionEntity.id == role_permissions_table.c.permission_id,
            isouter=True,
        )
        .where(user_roles_table.c.user_id == user_id)
    )

    rows = db.execute(base).all()
    return [
        RoleRow(
            scope_type=r.scope_type,
            scope_id=r.scope_id,
            isActiveOrg=r.isActiveOrg,
            role_id=r.role_id,
            role_name=r.role_name,
            permission_name=r.permission_name,
        )
        for r in rows
    ]


def fetch_sis_by_ids(db: Session, ids: Set[int]) -> Dict[int, SIEntity]:
    if not ids:
        return {}
    records = db.scalars(select(SIEntity).where(SIEntity.id.in_(ids))).all()
    return {x.id: x for x in records}


def fetch_orgs_by_ids(db: Session, ids: Set[int]) -> Dict[int, OrganizationEntity]:
    if not ids:
        return {}
    records = db.scalars(
        select(OrganizationEntity).where(OrganizationEntity.id.in_(ids))
    ).all()
    return {x.id: x for x in records}


def fetch_orgs_under_si_ids(
    db: Session, si_ids: Set[int]
) -> Dict[int, List[OrganizationEntity]]:
    """Return {si_id: [orgs...]} in a single batched query."""
    if not si_ids:
        return {}
    orgs = db.scalars(
        select(OrganizationEntity).where(OrganizationEntity.si_id.in_(si_ids))
    ).all()
    by_si: Dict[int, List[OrganizationEntity]] = defaultdict(list)
    for org in orgs:
        by_si[org.si_id].append(org)
    return by_si


def fetch_all_sis_and_orgs(
    db: Session,
) -> Tuple[List[SIEntity], List[OrganizationEntity]]:
    all_si = db.scalars(select(SIEntity)).all()
    all_org = db.scalars(select(OrganizationEntity)).all()
    return all_si, all_org
