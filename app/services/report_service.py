from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.dtos.common_dto import TextResponseDTO
from app.dtos.report_dto import (
    ReportGroupSetItemDTO,
    ReportGroupSetListResponseDTO,
    ReportGroupSetCreateResponseDTO,
    ReportGroupItemDTO,
    ReportGroupListResponseDTO,
    ReportGroupCreateResponseDTO,
    ReportGroupOrderItemDTO,
    ReportItemDTO,
    ReportListResponseDTO,
    ReportBatchUpdateItemDTO,
)
from app.domain.exception.domain_exception import DomainException
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
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.view"),
    )

    sets = report_repository.get_report_group_sets_by_org(db, org_id)
    items = [ReportGroupSetItemDTO(**set_data) for set_data in sets]

    return ReportGroupSetListResponseDTO(report_group_sets=items)


@db_tx
def create_report_group_set(
    db: Session, si_id: int, org_id: int, name: str, user: UserReadDTO
) -> ReportGroupSetCreateResponseDTO:
    """Create a new report group set"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.edit"),
    )

    new_set = report_repository.create_report_group_set(db, org_id, name)

    return ReportGroupSetCreateResponseDTO(
        rawData=ReportGroupSetItemDTO(id=new_set.id, name=new_set.name)
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
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.edit"),
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
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.edit"),
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


@db_tx
def get_report_groups(
    db: Session, si_id: int, org_id: int, report_group_set_id: int, user: UserReadDTO
) -> ReportGroupListResponseDTO:
    """Get all report groups for a report group set"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="pass"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    has_access = report_repository.check_user_report_group_set_access(
        db, user.id, report_group_set_id
    )
    if not has_access:
        raise DomainException("No access to this report group set", "no_access", 403)

    groups = report_repository.get_report_groups_by_set_id(db, report_group_set_id)
    items = [ReportGroupItemDTO(**group_data) for group_data in groups]

    return ReportGroupListResponseDTO(report_groups=items)


@db_tx
def create_report_group(
    db: Session,
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    name: str,
    logo: str | None,
    order: int,
    user: UserReadDTO,
) -> ReportGroupCreateResponseDTO:
    """Create a new report group"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.edit"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    if report_repository.check_report_group_order_exists(
        db, report_group_set_id, order
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "type": "duplicate_order",
                "msg": "Order already exists in this report group set",
            },
        )

    new_group = report_repository.create_report_group(
        db, report_group_set_id, name, logo, order
    )

    return ReportGroupCreateResponseDTO(
        rawData=ReportGroupItemDTO(
            report_group_set_id=new_group.report_group_set_id,
            id=new_group.id,
            name=new_group.name,
            logo=new_group.logo,
            order=new_group.order,
            counts=0,
        )
    )


@db_tx
def update_report_group(
    db: Session,
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    report_group_id: int,
    name: str,
    logo: str | None,
    user: UserReadDTO,
) -> TextResponseDTO:
    """Update report group name and logo"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.edit"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    report_group = report_repository.get_report_group_by_id(
        db, report_group_id, report_group_set_id
    )

    if not report_group:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group not found"},
        )

    report_repository.update_report_group(db, report_group_id, name, logo)

    return TextResponseDTO(
        status="success", message="Report group updated successfully"
    )


@db_tx
def update_report_group_orders(
    db: Session,
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    orders: list[ReportGroupOrderItemDTO],
    user: UserReadDTO,
) -> TextResponseDTO:
    """Update order for multiple report groups"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.edit"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    order_values = [order_item.order for order_item in orders]
    if len(order_values) != len(set(order_values)):
        raise HTTPException(
            status_code=400,
            detail={
                "type": "duplicate_order",
                "msg": "Duplicate order values in request",
            },
        )

    for order_item in orders:
        report_group = report_repository.get_report_group_by_id(
            db, order_item.report_group_id, report_group_set_id
        )

        if not report_group:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": "not_found",
                    "msg": f"Report group {order_item.report_group_id} not found",
                },
            )

        report_repository.update_report_group_order(
            db, order_item.report_group_id, order_item.order
        )

    return TextResponseDTO(
        status="success", message="Report group orders updated successfully"
    )


@db_tx
def delete_report_group(
    db: Session,
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    report_group_id: int,
    user: UserReadDTO,
) -> TextResponseDTO:
    """Delete report group and all its reports (cascade)"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.group.edit"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    report_group = report_repository.get_report_group_by_id(
        db, report_group_id, report_group_set_id
    )

    if not report_group:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group not found"},
        )

    report_repository.delete_report_group(db, report_group_id)

    return TextResponseDTO(
        status="success",
        message="Report group and all associated reports deleted successfully",
    )


@db_tx
def get_reports(
    db: Session,
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    report_group_id: int,
    user: UserReadDTO,
) -> ReportListResponseDTO:
    """Get all reports for a report group"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="pass"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    report_group = report_repository.get_report_group_by_id(
        db, report_group_id, report_group_set_id
    )

    if not report_group:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group not found"},
        )

    has_access = report_repository.check_user_report_group_set_access(
        db, user.id, report_group_set_id
    )
    if not has_access:
        raise DomainException("No access to this report group set", "no_access", 403)

    reports = report_repository.get_reports_by_group_id(db, report_group_id)
    items = [ReportItemDTO(**report_data) for report_data in reports]

    return ReportListResponseDTO(reports=items)


@db_tx
def batch_update_reports(
    db: Session,
    si_id: int,
    org_id: int,
    report_group_set_id: int,
    report_group_id: int,
    reports: list[ReportBatchUpdateItemDTO],
    user: UserReadDTO,
) -> TextResponseDTO:
    """Batch update reports: create new, update existing, delete missing"""
    verify_user_permission(
        db,
        user,
        PermissionCheckParams(si_id=si_id, org_id=org_id, perm="report.edit"),
    )

    report_group_set = report_repository.get_report_group_set_by_id(
        db, report_group_set_id, org_id
    )

    if not report_group_set:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group set not found"},
        )

    report_group = report_repository.get_report_group_by_id(
        db, report_group_id, report_group_set_id
    )

    if not report_group:
        raise HTTPException(
            status_code=404,
            detail={"type": "not_found", "msg": "Report group not found"},
        )

    existing_reports = report_repository.get_reports_by_group_id(db, report_group_id)
    existing_ids = {report["id"] for report in existing_reports}

    incoming_ids = {report.id for report in reports if report.id is not None}

    ids_to_delete = existing_ids - incoming_ids

    for report_id in ids_to_delete:
        report_repository.delete_report(db, report_id)

    for report_item in reports:
        if report_item.id is None:
            report_repository.create_report(
                db,
                report_group_id,
                report_item.name,
                report_item.looker_url,
                report_item.order,
            )
        else:
            existing_report = report_repository.get_report_by_id(
                db, report_item.id, report_group_id
            )
            if existing_report:
                report_repository.update_report(
                    db,
                    report_item.id,
                    report_item.name,
                    report_item.looker_url,
                    report_item.order,
                )
            else:
                report_repository.create_report(
                    db,
                    report_group_id,
                    report_item.name,
                    report_item.looker_url,
                    report_item.order,
                )

    return TextResponseDTO(status="success", message="Reports updated successfully")
