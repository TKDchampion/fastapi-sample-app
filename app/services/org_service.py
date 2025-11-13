import logging
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.repositories import (
    business_module_repository,
    org_repository,
    role_repository,
    user_repository,
)
from app.dtos.org_dto import (
    OrgUpsertRequestDTO,
    OrgUpsertResponseDTO,
    OrgListItemDTO,
    OrgListResponseDTO,
)

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
    db: Session, dto: OrgUpsertRequestDTO, si_id: int
) -> OrgUpsertResponseDTO:
    try:
        if dto.org_id:
            org = org_repository.upsert_org(db, dto, si_id, dto.org_id)
        else:
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

    except ValueError as e:
        logger.warning("Value error: %s", e)
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail={"type": "error", "msg": str(e)},
        )
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
