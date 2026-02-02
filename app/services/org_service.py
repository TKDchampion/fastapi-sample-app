import logging
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.domain.exception.domain_exception import DomainException
from app.dtos.common_dto import TextResponseDTO
from app.dtos.user_dto import UserReadDTO
from app.repositories import (
    business_module_repository,
    org_repository,
    role_repository,
    user_repository,
)
from app.dtos.org_dto import (
    OrgDetailDTO,
    OrgUpsertParamDTO,
    OrgUpsertResponseDTO,
    OrgListItemDTO,
    OrgListResponseDTO,
)
from app.dtos.report_dto import OrgSidebarResponseDTO
from app.services.permission_guard_service import verify_user_permission

logger = logging.getLogger(__name__)


@db_tx
def get_organizations_by_si_id(db: Session, si_id: int, user_id: int):
    user_roles = user_repository.get_user_roles(db, user_id)

    has_si_or_super_scope = any(
        (r.scope_type == "si" and r.scope_id == si_id) or r.scope_type == "super"
        for r in user_roles
    )

    if has_si_or_super_scope:
        orgs = org_repository.get_orgs_by_sid(db, si_id)
    else:
        allowed_org_ids = [r.scope_id for r in user_roles if r.scope_type == "org"]
        if not allowed_org_ids:
            return OrgListResponseDTO(org=[])
        orgs = org_repository.get_orgs_by_sid_oids(db, si_id, allowed_org_ids)

    if not orgs:
        return OrgListResponseDTO(org=[])

    items = [OrgListItemDTO(**org) for org in orgs]

    return OrgListResponseDTO(org=items)


@db_tx
def get_org_by_sid_oid(db: Session, si_id: int, org_id: int, user_info: UserReadDTO):
    params = PermissionCheckParams(si_id=si_id, org_id=org_id, perm="pass")
    res = verify_user_permission(db, user_info, params)

    return OrgDetailDTO.model_validate(res["org_detail"])


@db_tx
def upsert_organization_with_roles(
    db: Session, dto: OrgUpsertParamDTO, si_id: int, user_info: UserReadDTO
) -> OrgUpsertResponseDTO:
    if dto.org_id:
        params = PermissionCheckParams(si_id=si_id, org_id=dto.org_id, perm="org.edit")
        verify_user_permission(db, user_info, params)
        org = org_repository.upsert_org(db, dto, si_id, dto.org_id)
    else:
        params = PermissionCheckParams(si_id=si_id, perm="org.create")
        verify_user_permission(db, user_info, params)
        org = org_repository.upsert_org(db, dto, si_id)
        role_repository.create_roles(db, org)
    business_modules = business_module_repository.add_org_business_module(
        db, org.id, dto.business_modules
    )

    org_dict = {
        "id": org.id,
        "name": org.name,
        "logo": org.logo,
        "disabled": org.disabled,
        "contract_start": org.contract_start,
        "contract_end": org.contract_end,
        "created_at": org.created_at,
        "updated_at": org.updated_at,
        "business_modules": business_modules,
    }
    res = OrgUpsertResponseDTO.model_validate(org_dict)

    db.commit()
    db.refresh(org)
    return res


@db_tx
def update_organization_disabled(
    db: Session, user_info: UserReadDTO, si_id: int, org_id: int, disabled: bool
):
    params = PermissionCheckParams(si_id=si_id, org_id=org_id, perm="org.edit")
    verify_user_permission(db, user_info, params)
    org = org_repository.update_org_disabled(db, org_id, disabled)

    if not org:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "no_access",
                "msg": "No org access",
            },
        )

    return TextResponseDTO(
        status="success",
        message=f"Org updated successfully for org_id={org_id}, disabled={disabled}",
    )


@db_tx
def get_users_by_si_and_org(
    db: Session, si_id: int, org_id: int, user_info: UserReadDTO
):
    params = PermissionCheckParams(si_id=si_id, org_id=org_id, perm="member.view")
    verify_user_permission(db, user_info, params)
    si_org_ids = org_repository.get_orgs_by_sid(db, si_id)
    org_ids = [org.id for org in si_org_ids]
    is_org_under_si = org_id in org_ids

    if not is_org_under_si:
        raise DomainException(f"Not Found Organization {org_id}", "org_not_found", 404)

    users = org_repository.get_users_by_si_and_org(db, si_id, org_id)

    user_map = {}

    for user in users:
        user_id = user.user_id
        role_name = user.role_name or "owner"

        if user_id not in user_map:
            user_map[user_id] = {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "picture": user.picture,
                "role_name": role_name,
                "role_id": user.role_id,
                "report_group_set": [],
            }
        else:
            # 處理 role_name 優先級（owner 優先）
            if role_name == "owner" and user_map[user_id]["role_name"] != "owner":
                user_map[user_id]["role_name"] = "owner"
                user_map[user_id]["role_id"] = user.role_id

        # 收集 report_group_set（避免重複）
        if user.report_group_set_id is not None:
            rgs_entry = {
                "id": user.report_group_set_id,
                "name": user.report_group_set_name,
            }
            if rgs_entry not in user_map[user_id]["report_group_set"]:
                user_map[user_id]["report_group_set"].append(rgs_entry)

    return list(user_map.values())


@db_tx
def get_org_sidebar(
    db: Session, si_id: int, org_id: int, current_user: UserReadDTO
) -> OrgSidebarResponseDTO:
    """獲取當前用戶在特定組織下的 sidebar 資料（report_groups_sets 和 business_modules）"""
    verify_user_permission(
        db,
        current_user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="pass"),
    )

    report_groups_sets = user_repository.get_user_report_groups_grouped(
        db, current_user.id, org_id
    )
    business_modules = org_repository.get_org_business_modules(db, org_id)

    return OrgSidebarResponseDTO(
        report_groups_sets=report_groups_sets,
        business_modules=business_modules,
    )
