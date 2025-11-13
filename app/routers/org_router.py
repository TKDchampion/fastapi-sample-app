import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.org_dto import (
    LogoUploadResponseDTO,
    OrgUpsertRequestDTO,
    OrgUpsertResponseDTO,
    OrgListResponseDTO,
)
from app.entities.organization_entity import OrganizationEntity
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
    # user_info: UserReadDTO = Depends(token_required),
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
    # user_info: UserReadDTO = Depends(token_required),
) -> OrgUpsertResponseDTO:
    """Create organization and upload logo to GCS"""

    try:
        return org_service.upsert_organization_with_roles(db, org, si_id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Create organization error"},
        )
