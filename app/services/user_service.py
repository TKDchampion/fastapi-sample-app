from collections import defaultdict
from typing import List
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.build_si_map import build_si_map
from app.domain.access_tree.build_super_tree import build_super_tree
from app.domain.access_tree.fill_si_full_access import fill_si_full_access
from app.domain.access_tree.merge_org_permissions import merge_org_permissions
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.domain.exception.domain_exception import DomainException
from app.repositories import permission_repository, user_repository
from app.services.permission_guard_service import verify_user_permission
from app.dtos.user_dto import (
    UserCreateDTO,
    UserReadDTO,
)
from app.dtos.common_dto import TextResponseDTO
from app.dtos.report_dto import UserReportGroupItemDTO


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


@db_tx
def set_user_report_group_sets(
    db: Session,
    si_id: int,
    org_id: int,
    target_user_id: int,
    group_set_ids: List[int],
    current_user: UserReadDTO,
) -> TextResponseDTO:
    """設定 user 的 report group set accesses，會取代原有的所有 accesses"""
    # 驗證操作者權限
    verify_user_permission(
        db,
        current_user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="member.edit"),
    )

    # 驗證目標 user 是否存在
    target_user = user_repository.get_user_by_id(db, target_user_id)
    if not target_user:
        raise DomainException("not_found", "User not found", 404)

    # 驗證 group_set_ids 是否都屬於該 org
    if group_set_ids:
        valid_group_sets = user_repository.get_report_group_sets_by_ids_and_org(
            db, group_set_ids, org_id
        )
        valid_ids = {gs.id for gs in valid_group_sets}
        invalid_ids = set(group_set_ids) - valid_ids
        if invalid_ids:
            raise DomainException(
                "invalid_group_set",
                f"Report group set IDs {list(invalid_ids)} do not belong to this organization",
                400,
            )

    # 執行取代
    user_repository.replace_user_report_group_set_accesses(
        db, target_user_id, group_set_ids
    )

    return TextResponseDTO(
        status="success",
        message="User report group set accesses updated",
    )


# @db_tx
# def get_user_report_groups(
#     db: Session,
#     si_id: int,
#     org_id: int,
#     current_user: UserReadDTO,
# ) -> List[UserReportGroupItemDTO]:
#     """獲取當前用戶在特定組織下可訪問的所有 report_groups"""
#     # 驗證用戶對該 org 的訪問權限
#     verify_user_permission(
#         db,
#         current_user,
#         PermissionCheckParams(si_id=si_id, org_id=org_id, perm="pass"),
#     )

#     return user_repository.get_user_report_groups(db, current_user.id, org_id)
