from collections import defaultdict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.domain.access_tree.build_si_map import build_si_map
from app.domain.access_tree.build_super_tree import build_super_tree
from app.domain.access_tree.fill_si_full_access import fill_si_full_access
from app.domain.access_tree.merge_org_permissions import merge_org_permissions
from app.entities.si_entity import SIEntity
from app.repositories import user_repository
from app.dtos.user_dto import (
    UserCreateDTO,
    UserSIListItemDTO,
    UserSIListResponseDTO,
)


def get_users(db: Session):
    return user_repository.get_all_users(db)


def add_user(db: Session, user: UserCreateDTO):
    return user_repository.create_user(db, user)


def get_user_by_email(db: Session, email: str):
    return user_repository.get_user_by_email(db, email)


def get_user_access_tree(db: Session, user_id: int):
    user = user_repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles = user_repository.get_user_roles_si_org_perm(db, user_id)
    perms = user_repository.get_permissions(db)

    perms_by_type = defaultdict(list)
    for name, ptype in perms:
        perms_by_type[ptype].append(name)

    has_super = any(r.scope_type == "super" for r in roles)

    result = {
        "level": "super",
        "isActive": has_super,
        "permissions": perms_by_type["super"] if has_super else [],
        "accessibleNode": [],
    }

    if has_super:
        # super = full tree
        return build_super_tree(user, perms_by_type, result, db)

    # else: normal tree
    si_map = build_si_map(roles, perms_by_type)
    merge_org_permissions(si_map)
    fill_si_full_access(si_map, perms_by_type, db)

    result["accessibleNode"] = list(si_map.values())

    return {
        "user": user,
        "permissionTree": result,
    }


def get_user_si(db: Session, user_id: int):
    user = user_repository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles = user_repository.get_user_roles(db, user_id)
    has_super = any(r.scope_type == "super" for r in roles)

    if has_super:
        sis = user_repository.get_si_all(db)

    sis = user_repository.get_si_user_roles(db, user_id)
    items = [UserSIListItemDTO.model_validate(row) for row in sis]

    return UserSIListResponseDTO(si=items)
