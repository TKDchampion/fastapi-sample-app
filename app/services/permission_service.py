from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.domain.exception.domain_exception import DomainException
from app.dtos.permission_dto import RolePermissionDTO, RolePermissionUpdateDTO
from app.dtos.user_dto import UserReadDTO
from app.repositories import permission_repository, role_repository, org_repository
from app.services.permission_guard_service import verify_user_permission


@db_tx
def get_role_permissions(
    db: Session,
    si_id: int,
    org_id: int,
    user_info: UserReadDTO,
):
    params = PermissionCheckParams(si_id=si_id, org_id=org_id, perm="org.permission.view")
    verify_user_permission(db, user_info, params)
    roles = permission_repository.get_roles_with_permissions(db, org_id)

    response = []
    for role in roles:
        response.append(
            RolePermissionDTO(
                id=role.id,
                name=role.name,
                permissions=[perm.id for perm in role.permissions],
            )
        )

    return response


@db_tx
def get_all_permissions_org(db: Session, org_id: int):
    permissions = permission_repository.get_all_permissions_org(db)

    # 取得該組織的 business modules keys
    org_business_modules = org_repository.get_org_business_modules(db, org_id)
    org_business_keys = {bm.key for bm in org_business_modules}

    result = []
    for perm in permissions:
        key = perm["key"]
        # 如果 key 以 "business." 開頭，只有當對應的 business module key 存在於組織中才加入
        if key.startswith("business."):
            # 取得 "business." 後面的部分作為 business module key
            business_key = key.split(".")[1] if len(key.split(".")) > 1 else None
            if business_key and business_key in org_business_keys:
                result.append(perm)
        else:
            # 非 business. 開頭的 permission 全部 return
            result.append(perm)

    return result


@db_tx
def update_role_permissions(
    db: Session,
    si_id: int,
    org_id: int,
    role_permissions: list[RolePermissionUpdateDTO],
    user_info: UserReadDTO,
):
    # 1. Validate role_ids belong to the org
    roles = role_repository.roles_by_org(db, org_id)
    existing_role_ids = {r["id"] for r in roles}
    requested_role_ids = {rp.id for rp in role_permissions}

    if requested_role_ids != existing_role_ids:
        raise DomainException(
            "Some role_ids do not belong to this organization",
            "org_not_found",
            404,
        )

    # 2. Validate user permission
    params = PermissionCheckParams(si_id=si_id, org_id=org_id, perm="org.permission.edit")
    verify_user_permission(db, user_info, params)

    # 3. Load all valid permission ids (org-only)
    permissions = permission_repository.get_all_permissions_org(db)
    valid_permission_ids = {p["id"] for p in permissions}

    # 4. Collect ALL invalid permission ids across all roles (no multiple loops)
    invalid_ids = {
        pid
        for rp in role_permissions
        for pid in rp.permissions
        if pid not in valid_permission_ids
    }

    if invalid_ids:
        raise DomainException(
            f"Invalid permission ids: {list(invalid_ids)}",
            "invalid_permission",
            400,
        )

    # 5. Update: each role_id one shot
    for rp in role_permissions:
        permission_repository.delete_role_permissions(db, rp.id)
        permission_repository.add_role_permissions(db, rp.id, rp.permissions)

    # 6. Return updated data (within same transaction)
    roles = permission_repository.get_roles_with_permissions(db, org_id)

    response = []
    for role in roles:
        response.append(
            RolePermissionDTO(
                id=role.id,
                name=role.name,
                permissions=[perm.id for perm in role.permissions],
            )
        )

    return response
