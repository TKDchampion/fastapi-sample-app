import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.domain.org_form.org_form_create_parser import parse_org_create_form
from app.dtos.org_dto import OrgCreateRequestDTO, OrgListItemDTO, OrgListResponseDTO
from app.entities.organization_entity import OrganizationEntity
from app.repositories.org_repository import upsert_org, get_by_name
from app.repositories.role_repository import create_roles
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
        return org_service.get_organizations_by_si_id(db, si_id)
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
    "/upsert/{si_id}",
    response_model=OrgListItemDTO,
    summary="Create new organization under SI",
    description="Create a new organization under a given SI and upload logo to GCS.",
)
def upsert_organization(
    si_id: int,
    dto: OrgCreateRequestDTO = Depends(parse_org_create_form),
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    # user_info: UserReadDTO = Depends(token_required),
) -> OrgListItemDTO:
    """Create organization and upload logo to GCS"""
    if get_by_name(db, dto.name):
        raise HTTPException(status_code=400, detail="Organization name already exists")

    logo_url = upload_logo_to_gcs(logo) if logo else None
    dto.logo = logo_url

    try:
        return org_service.upsert_organization_with_roles(db, dto, si_id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Create organization error"},
        )
