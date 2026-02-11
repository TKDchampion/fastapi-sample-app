from fastapi import APIRouter
from fastapi.params import Depends
from app.database import get_db
from app.decorators import router_try
from app.dtos.report_dto import (
    OrgSidebarResponseDTO,
    ReportGroupListResponseDTO,
    ReportListResponseDTO,
)
from sqlalchemy.orm import Session

from app.dtos.user_dto import UserReadDTO
from app.services import org_service, report_service
from app.services.jwt_service import token_required


router = APIRouter(prefix="/sidebar", tags=["Sidebar"])


@router.get("/si/{si_id}/org/{org_id}", response_model=OrgSidebarResponseDTO)
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


@router.get(
    "/si/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}/report_group/{report_group_id}/report",
    response_model=ReportListResponseDTO,
)
@router_try()
def get_reports(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    report_group_id: int,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> ReportListResponseDTO:
    """Get all reports for a report group"""
    return report_service.get_reports(
        db, si_id, org_id, report_group_set_id, report_group_id, user
    )
