from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.dtos.common_dto import TextResponseDTO
from app.dtos.report_dto import (
    ReportGroupSetCreateRequestDTO,
    ReportGroupSetListResponseDTO,
    ReportGroupCreateRequestDTO,
    ReportGroupListResponseDTO,
    ReportGroupUpdateRequestDTO,
    ReportGroupOrderUpdateRequestDTO,
    ReportListResponseDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.services import report_service
from app.services.jwt_service import token_required


router = APIRouter(prefix="/si", tags=["Report"])


@router.get(
    "/{si_id}/org/{org_id}/report_group_set",
    response_model=ReportGroupSetListResponseDTO,
)
@router_try()
def get_report_group_sets(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> ReportGroupSetListResponseDTO:
    """Get all report group sets for an organization"""
    return report_service.get_report_group_sets(db, si_id, org_id, user)


@router.post(
    "/{si_id}/org/{org_id}/report_group_set",
    response_model=TextResponseDTO,
)
@router_try()
def create_report_group_set(
    si_id: int,
    org_id: int,
    body: ReportGroupSetCreateRequestDTO,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Create a new report group set"""
    return report_service.create_report_group_set(db, si_id, org_id, body.name, user)


@router.put(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}",
    response_model=TextResponseDTO,
)
@router_try()
def update_report_group_set(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    body: ReportGroupSetCreateRequestDTO,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Update report group set name"""
    return report_service.update_report_group_set(
        db, si_id, org_id, report_group_set_id, body.name, user
    )


@router.delete(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}",
    response_model=TextResponseDTO,
)
@router_try()
def delete_report_group_set(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Delete report group set and all its report groups"""
    return report_service.delete_report_group_set(
        db, si_id, org_id, report_group_set_id, user
    )


@router.get(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}/report_group",
    response_model=ReportGroupListResponseDTO,
)
@router_try()
def get_report_groups(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> ReportGroupListResponseDTO:
    """Get all report groups for a report group set"""
    return report_service.get_report_groups(db, si_id, org_id, report_group_set_id, user)


@router.post(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}/report_group",
    response_model=TextResponseDTO,
)
@router_try()
def create_report_group(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    body: ReportGroupCreateRequestDTO,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Create a new report group"""
    return report_service.create_report_group(
        db, si_id, org_id, report_group_set_id, body.name, body.logo, body.order, user
    )


@router.put(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}/report_group/{report_group_id}",
    response_model=TextResponseDTO,
)
@router_try()
def update_report_group(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    report_group_id: int,
    body: ReportGroupUpdateRequestDTO,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Update report group name and logo"""
    return report_service.update_report_group(
        db, si_id, org_id, report_group_set_id, report_group_id, body.name, body.logo, user
    )


@router.put(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}/report_group",
    response_model=TextResponseDTO,
)
@router_try()
def update_report_group_orders(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    body: ReportGroupOrderUpdateRequestDTO,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Update order for multiple report groups"""
    return report_service.update_report_group_orders(
        db, si_id, org_id, report_group_set_id, body.orders, user
    )


@router.delete(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}/report_group/{report_group_id}",
    response_model=TextResponseDTO,
)
@router_try()
def delete_report_group(
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    report_group_id: int,
    db: Session = Depends(get_db),
    user: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """Delete report group and all its associated reports"""
    return report_service.delete_report_group(
        db, si_id, org_id, report_group_set_id, report_group_id, user
    )


@router.get(
    "/{si_id}/org/{org_id}/report_group_set/{report_group_set_id}/report_group/{report_group_id}/report",
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
