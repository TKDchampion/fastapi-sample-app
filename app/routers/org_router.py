import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.common_dto import TextResponseDTO
from app.dtos.org_dto import (
    LogoUploadResponseDTO,
    OrgUpsertRequestDTO,
    OrgUpsertResponseDTO,
    OrgListResponseDTO,
)
from app.services import org_service
from app.dtos.user_dto import (
    UserReadDTO,
)
from app.services.gcs_uploader import upload_logo_to_gcs
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/org", tags=["Org"])


@router.get("/list/{si_id}", response_model=OrgListResponseDTO)
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


@router.post(
    "/upload-logo",
    summary="Upload organization logo to GCS",
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
            detail={"type": "error", "msg": "Create organization error"},
        )


@router.post(
    "/upsert/{si_id}",
    response_model=OrgUpsertResponseDTO,
    summary="Create new organization under SI",
    description="Create a new organization under a given SI and upload logo to GCS.",
)
def upsert_organization(
    si_id: int,
    org: OrgUpsertRequestDTO,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> OrgUpsertResponseDTO:
    """Create organization and upload logo to GCS"""

    try:
        return org_service.upsert_organization_with_roles(db, org, si_id, user_info)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Create organization error"},
        )


@router.put(
    "/is_active/{si_id}/{org_id}",
    response_model=TextResponseDTO,
    summary="Update org is_active",
    description="Update this org is_active",
)
def upsert_organization(
    si_id: int,
    org_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Create organization and upload logo to GCS"""

    try:
        return org_service.update_organization_isActive_with_roles(
            db, user_info, si_id, org_id, is_active
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
