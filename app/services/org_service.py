import logging
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.domain.access_tree.check_user_access import OrgWriteParams
from app.dtos.common_dto import TextResponseDTO
from app.dtos.user_dto import UserReadDTO, UserRolesResponseDTO
from app.repositories import (
    business_module_repository,
    org_repository,
    role_repository,
    user_repository,
)
from app.dtos.org_dto import (
    OrgUpsertParamDTO,
    OrgUpsertResponseDTO,
    OrgListItemDTO,
    OrgListResponseDTO,
)
from app.services.permission_guard_service import verify_org_write_permission

logger = logging.getLogger(__name__)


def get_organizations_by_si_id(db: Session, si_id: int, user_id: int):
    user_roles = user_repository.get_user_roles(db, user_id)

    has_si_or_super_scope = any(
        (r.scope_type == "si" and r.scope_id == si_id) or r.scope_type == "super"
        for r in user_roles
    )

    if has_si_or_super_scope:
        orgs = org_repository.get_orgs_by_si_id(db, si_id)
    else:
        allowed_org_ids = [r.scope_id for r in user_roles if r.scope_type == "org"]
        if not allowed_org_ids:
            return OrgListResponseDTO(org=[])
        orgs = org_repository.get_orgs_ids_by_si(db, si_id, allowed_org_ids)

    if not orgs:
        return OrgListResponseDTO(org=[])

    items = [OrgListItemDTO.model_validate(org, from_attributes=True) for org in orgs]

    return OrgListResponseDTO(org=items)


def upsert_organization_with_roles(
    db: Session, dto: OrgUpsertParamDTO, si_id: int, user_info: UserReadDTO
) -> OrgUpsertResponseDTO:
    try:
        if dto.org_id:
            params = OrgWriteParams(si_id=si_id, org_id=dto.org_id, perm="org.edit")
            verify_org_write_permission(db, user_info, params)
            org = org_repository.upsert_org(db, dto, si_id, dto.org_id)
        else:
            params = OrgWriteParams(si_id=si_id, perm="org.create")
            verify_org_write_permission(db, user_info, params)
            org = org_repository.upsert_org(db, dto, si_id)
            role_repository.create_roles(db, org)
        business_modules = business_module_repository.add_org_business_module(
            db, org.id, dto.business_modules
        )

        db.commit()
        db.refresh(org)
        return OrgUpsertResponseDTO.model_validate(
            {**org.__dict__, "business_modules": business_modules}, from_attributes=True
        )

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        logger.error("Exception message : %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={"type": "error", "msg": "db error"},
        )
    except SQLAlchemyError as e:
        logger.error("Exception message : %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "db create error"},
        )
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "create or update organization error"},
        )


def update_organization_disabled(
    db: Session, user_info: UserReadDTO, si_id: int, org_id: int, disabled: bool
):
    try:
        params = OrgWriteParams(si_id=si_id, org_id=org_id, perm="org.edit")
        verify_org_write_permission(db, user_info, params)
        org = org_repository.update_org_disabled(db, org_id, disabled)

        if not org:
            raise HTTPException(
                status_code=403,
                detail={
                    "type": "error",
                    "msg": f"No org access",
                },
            )

        return TextResponseDTO(
            status="success",
            message=f"Org updated successfully for org_id={org_id}, disabled={disabled}",
        )

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        logger.error("Exception message : %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={"type": "error", "msg": "db error"},
        )
    except SQLAlchemyError as e:
        logger.error("Exception message : %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "db create error"},
        )
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "create organization error"},
        )


# def get_users_by_si_and_org(
#     db: Session, si_id: int, org_id: int, user_info: UserReadDTO
# ):
def get_users_by_si_and_org(db: Session, si_id: int, org_id: int):
    try:
        # params = OrgWriteParams(si_id=si_id, org_id=org_id, perm="member.view")
        # verify_org_write_permission(db, user_info, params)
        users = org_repository.get_users_by_si_and_org(db, si_id, org_id)

        user_map = {}

        for user in users:
            user_id = user.user_id

            role_name = user.role_name or "owner"

            if user_id in user_map:
                if user_map[user_id]["role_name"] == "owner":
                    continue

                if role_name == "owner":
                    user_map[user_id] = {
                        "user_id": user.user_id,
                        "name": user.name,
                        "email": user.email,
                        "picture": user.picture,
                        "role_name": "owner",
                    }
                    continue

                # 否則 role_name 不是 owner → 如果 user 沒 owner，保持第一個
                continue

            user_map[user_id] = {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "picture": user.picture,
                "role_name": role_name,
            }

        return list(user_map.values())
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": f"get users from org error{e}"},
        )
