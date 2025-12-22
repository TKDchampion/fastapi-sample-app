from collections import defaultdict
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.build_si_map import build_si_map
from app.domain.access_tree.build_super_tree import build_super_tree
from app.domain.access_tree.fill_si_full_access import fill_si_full_access
from app.domain.access_tree.merge_org_permissions import merge_org_permissions
from app.repositories import permission_repository, user_repository
from app.dtos.user_dto import (
    UserCreateDTO,
    UserReadDTO,
)


@db_tx
def get_users(db: Session):
    return user_repository.get_all_users(db)


@db_tx
def add_user(db: Session, user: UserCreateDTO):
    return user_repository.create_user(db, user)


@db_tx
def get_user_by_email(db: Session, email: str):
    return user_repository.get_user_by_email(db, email)


@db_tx
def get_user_access_tree(db: Session, user: UserReadDTO):
    roles = user_repository.get_user_roles_si_org_perm(db, user.id)
    perms = permission_repository.get_permissions(db)

    perms_by_type = defaultdict(list)
    for key, ptype in perms:
        perms_by_type[ptype].append(key)

    has_super = any(r.scope_type == "super" for r in roles)

    result = {
        "level": "super",
        "isActive": has_super,
        "permissions": [p for p in perms_by_type["super"] if p] if has_super else [],
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
