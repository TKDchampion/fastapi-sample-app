from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.report_group_set_entity import ReportGroupSetEntity


def get_report_group_sets_by_org(db: Session, org_id: int):
    """Get all report group sets for an organization"""
    return (
        db.execute(
            select(
                ReportGroupSetEntity.id,
                ReportGroupSetEntity.name,
            ).where(ReportGroupSetEntity.org_id == org_id)
        )
        .mappings()
        .all()
    )


def create_report_group_set(db: Session, org_id: int, name: str):
    """Create a new report group set"""
    new_set = ReportGroupSetEntity(org_id=org_id, name=name)
    db.add(new_set)
    db.flush()
    return new_set


def get_report_group_set_by_id(db: Session, report_group_set_id: int, org_id: int):
    """Get report group set by ID and verify it belongs to the org"""
    return db.execute(
        select(ReportGroupSetEntity).where(
            ReportGroupSetEntity.id == report_group_set_id,
            ReportGroupSetEntity.org_id == org_id,
        )
    ).scalar_one_or_none()


def update_report_group_set_name(
    db: Session, report_group_set_id: int, name: str
) -> None:
    """Update report group set name"""
    report_group_set = db.execute(
        select(ReportGroupSetEntity).where(ReportGroupSetEntity.id == report_group_set_id)
    ).scalar_one_or_none()

    if report_group_set:
        report_group_set.name = name
        db.flush()


def delete_report_group_set(db: Session, report_group_set_id: int) -> None:
    """Delete report group set (cascade deletes report_groups automatically)"""
    report_group_set = db.execute(
        select(ReportGroupSetEntity).where(ReportGroupSetEntity.id == report_group_set_id)
    ).scalar_one_or_none()

    if report_group_set:
        db.delete(report_group_set)
        db.flush()
