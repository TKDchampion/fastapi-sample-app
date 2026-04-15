from datetime import datetime, time, timezone
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.dtos.common_dto import TextResponseDTO
from app.dtos.org_dto import (
    LogoUploadResponseDTO,
    OrgDetailDTO,
    OrgUpsertParamDTO,
    OrgUpsertRequestDTO,
    OrgUpsertResponseDTO,
    OrgListResponseDTO,
)
from app.dtos.report_dto import OrgSidebarResponseDTO
from app.dtos.tableau_dto import TableauTokenResponseDTO
from app.services import org_service
from app.services.tableau_service import issue_tableau_token
from app.dtos.user_dto import (
    UserReadDTO,
)
from app.services.gcs_uploader import upload_logo_to_gcs
from app.services.jwt_service import token_required


org_router = APIRouter(prefix="/org", tags=["Org"])
si_router = APIRouter(prefix="/si", tags=["Org"])


@si_router.get("/{si_id}/org/list", response_model=OrgListResponseDTO)
@router_try()
def get_organizations_by_si_id(
    si_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> OrgListResponseDTO:
    """
    Get organizations by SI ID
    """
    return org_service.get_organizations_by_si_id(db, si_id, user_info.id)


@org_router.post(
    "/upload_logo",
    response_model=LogoUploadResponseDTO,
)
@router_try()
def upload_organization_logo(
    logo: UploadFile = File(...),
    user_info: UserReadDTO = Depends(token_required),
):
    """Upload organization logo to GCS"""
    logo_url = upload_logo_to_gcs(logo) if logo else None
    return {"url": logo_url}


@si_router.post(
    "/{si_id}/org/create",
    response_model=OrgUpsertResponseDTO,
)
@router_try()
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

    return org_service.upsert_organization_with_roles(db, org_body, si_id, user_info)


@si_router.put(
    "/{si_id}/org/{org_id}/update",
    response_model=OrgUpsertResponseDTO,
)
@router_try()
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

    return org_service.upsert_organization_with_roles(db, org_body, si_id, user_info)


@si_router.put(
    "/{si_id}/org/{org_id}/disabled",
    response_model=TextResponseDTO,
)
@router_try()
def upsert_organization(
    si_id: int,
    org_id: int,
    disabled: bool,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Update organization and upload logo to GCS"""

    return org_service.update_organization_disabled(
        db, user_info, si_id, org_id, disabled
    )


@si_router.get("/{si_id}/org/{org_id}/detail", response_model=OrgDetailDTO)
@router_try()
def get_org_by_sid_oid(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """Get organization detail"""

    return org_service.get_org_by_sid_oid(db, si_id, org_id, user_info)


@si_router.get(
    "/{si_id}/org/{org_id}/sidebar",
    deprecated=True,
    response_model=OrgSidebarResponseDTO,
)
@router_try()
def get_org_sidebar(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> OrgSidebarResponseDTO:
    """
    Get sidebar data for a specific organization.
    Returns report groups accessible by the current user and business modules of the org.
    """
    return org_service.get_org_sidebar(db, si_id, org_id, user_info)


@si_router.post(
    "/{si_id}/org/{org_id}/tableau",
    response_model=TableauTokenResponseDTO,
)
@router_try()
def get_tableau_token(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> TableauTokenResponseDTO:
    """
    Issue a Tableau JWT for the current user after org/report access verification.
    """
    return issue_tableau_token(db, si_id, org_id, user_info)
