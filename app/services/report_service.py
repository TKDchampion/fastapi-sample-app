from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.dtos.common_dto import TextResponseDTO
from app.dtos.report_dto import (
    ReportGroupSetItemDTO,
    ReportGroupSetListResponseDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.repositories import report_repository
from app.services.permission_guard_service import verify_user_permission


@db_tx
def get_report_group_sets(
    db: Session, si_id: int, org_id: int, user: UserReadDTO
) -> ReportGroupSetListResponseDTO:
    """Get all report group sets for an organization"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="org.permission.view"),
    )

    sets = report_repository.get_report_group_sets_by_org(db, org_id)
    items = [ReportGroupSetItemDTO(**set_data) for set_data in sets]

    return ReportGroupSetListResponseDTO(report_group_sets=items)


@db_tx
def create_report_group_set(
    db: Session, si_id: int, org_id: int, name: str, user: UserReadDTO
) -> TextResponseDTO:
    """Create a new report group set"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="org.permission.edit"),
    )

    report_repository.create_report_group_set(db, org_id, name)

    return TextResponseDTO(
        status="success", message="Report group set created successfully"
    )


@db_tx
def update_report_group_set(
    db: Session,
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    name: str,
    user: UserReadDTO,
) -> TextResponseDTO:
    """Update report group set name"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="org.permission.edit"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    report_repository.update_report_group_set_name(db, report_group_set_id, name)

    return TextResponseDTO(
        status="success", message="Report group set updated successfully"
    )


@db_tx
def delete_report_group_set(
    db: Session, si_id: int, org_id: int, report_group_set_id: int, user: UserReadDTO
) -> TextResponseDTO:
    """Delete report group set and all its report groups (cascade)"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="org.permission.edit"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    report_repository.delete_report_group_set(db, report_group_set_id)

    return TextResponseDTO(
        status="success", message="Report group set deleted successfully"
    )
