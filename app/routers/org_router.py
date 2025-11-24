from datetime import datetime, time, timezone
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.common_dto import TextResponseDTO
from app.dtos.org_dto import (
    LogoUploadResponseDTO,
    OrgDetailDTO,
    OrgUpsertParamDTO,
    OrgUpsertRequestDTO,
    OrgUpsertResponseDTO,
    OrgListResponseDTO,
)
from app.services import org_service
from app.dtos.user_dto import (
    UserReadDTO,
    UserRolesResponseDTO,
)
from app.services.gcs_uploader import upload_logo_to_gcs
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)


org_router = APIRouter(prefix="/org", tags=["Org"])
si_router = APIRouter(prefix="/si", tags=["Org"])


@si_router.get("/{si_id}/org/list", response_model=OrgListResponseDTO)
def get_organizations_by_si_id(
    si_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> OrgListResponseDTO:
    """
    Get organizations by SI ID
    """
    try:
        return org_service.get_organizations_by_si_id(db, si_id, user_info.id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )


@org_router.post(
    "/upload_logo",
    response_model=LogoUploadResponseDTO,
)
def upload_organization_logo(
    logo: UploadFile = File(...),
    user_info: UserReadDTO = Depends(token_required),
):
    """Upload organization logo to GCS"""
    try:
        logo_url = upload_logo_to_gcs(logo) if logo else None
        return {"url": logo_url}

    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Upload organization logo error"},
        )


@si_router.post(
    "/{si_id}/org/create",
    response_model=OrgUpsertResponseDTO,
)
def create_organization(
    si_id: int,
    org: OrgUpsertRequestDTO,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> OrgUpsertResponseDTO:
    """Create organization and upload logo to GCS"""
    org_body = OrgUpsertParamDTO(**org.model_dump(), org_id=None)
    start_dt = datetime.combine(org.contract_start, time.min).replace(
        tzinfo=timezone.utc
    )
    end_dt = datetime.combine(org.contract_end, time.max).replace(tzinfo=timezone.utc)
    org_body.contract_start = start_dt
    org_body.contract_end = end_dt

    try:
        return org_service.upsert_organization_with_roles(
            db, org_body, si_id, user_info
        )
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Create organization error"},
        )


@si_router.put(
    "/{si_id}/org/{org_id}/update",
    response_model=OrgUpsertResponseDTO,
)
def update_organization(
    si_id: int,
    org: OrgUpsertRequestDTO,
    org_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> OrgUpsertResponseDTO:
    """Create organization and upload logo to GCS"""
    org_body = OrgUpsertParamDTO(**org.model_dump())
    start_dt = datetime.combine(org.contract_start, time.min).replace(
        tzinfo=timezone.utc
    )
    end_dt = datetime.combine(org.contract_end, time.max).replace(tzinfo=timezone.utc)
    org_body.contract_start = start_dt
    org_body.contract_end = end_dt

    if org_id:
        org_body.org_id = org_id

    try:
        return org_service.upsert_organization_with_roles(
            db, org_body, si_id, user_info
        )
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Create organization error"},
        )


@si_router.put(
    "/{si_id}/org/{org_id}/disabled",
    response_model=TextResponseDTO,
)
def upsert_organization(
    si_id: int,
    org_id: int,
    disabled: bool,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Update organization and upload logo to GCS"""

    try:
        return org_service.update_organization_disabled(
            db, user_info, si_id, org_id, disabled
        )
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Update organization error"},
        )


@si_router.get("/{si_id}/org/{org_id}/users", response_model=list[UserRolesResponseDTO])
def get_users_by_si_and_org(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """Get organization users"""

    try:
        return org_service.get_users_by_si_and_org(db, si_id, org_id, user_info)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Get organization users error"},
        )


@si_router.get("/{si_id}/org/{org_id}/detail", response_model=OrgDetailDTO)
def get_org_by_sid_oid(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """Get organization detail"""

    try:
        return org_service.get_org_by_sid_oid(db, si_id, org_id, user_info)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Get organization detail error"},
        )
