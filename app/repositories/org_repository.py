from typing import List
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, noload, selectinload
from app.dtos.org_dto import OrgUpsertParamDTO
from app.dtos.report_dto import BusinessModuleItemDTO
from app.entities.organization_entity import OrganizationEntity
from app.entities.business_module_entity import BusinessModuleEntity
from app.entities.associations_entity import (
    user_roles as user_roles_table,
    org_business_modules,
)
from app.entities.role_entity import RoleEntity
from app.entities.user_entity import UserEntity
from app.entities.user_report_group_set_access_entity import UserReportGroupSetAccessEntity
from app.entities.report_group_set_entity import ReportGroupSetEntity


def get_orgs_by_sid(db: Session, si_id: int):
    return (
        db.execute(
            select(
                OrganizationEntity.id,
                OrganizationEntity.name,
                OrganizationEntity.logo,
                OrganizationEntity.disabled,
                OrganizationEntity.contract_start,
                OrganizationEntity.contract_end,
                OrganizationEntity.created_at,
                OrganizationEntity.updated_at,
            ).where(OrganizationEntity.si_id == si_id)
        )
        .mappings()
        .all()
    )


def get_orgs_by_sid_oids(db: Session, si_id: int, ids: list[int]):
    return (
        db.execute(
            select(
                OrganizationEntity.id,
                OrganizationEntity.name,
                OrganizationEntity.logo,
                OrganizationEntity.disabled,
                OrganizationEntity.contract_start,
                OrganizationEntity.contract_end,
                OrganizationEntity.created_at,
                OrganizationEntity.updated_at,
            ).where(
                OrganizationEntity.si_id == si_id,
                OrganizationEntity.id.in_(ids),
            )
        )
        .mappings()
        .all()
    )


def get_org_by_sid_oid(db: Session, si_id: int, org_id: int):
    stmt = (
        select(OrganizationEntity)
        .options(selectinload(OrganizationEntity.business_modules))
        .where(
            OrganizationEntity.si_id == si_id,
            OrganizationEntity.id == org_id,
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def get_all_orgs(db: Session):
    return (
        db.execute(
            select(
                OrganizationEntity.id,
                OrganizationEntity.name,
                OrganizationEntity.si_id,
                OrganizationEntity.logo,
                OrganizationEntity.disabled,
                OrganizationEntity.contract_start,
                OrganizationEntity.contract_end,
            )
        )
        .mappings()
        .all()
    )


def upsert_org(
    db: Session,
    dto: OrgUpsertParamDTO,
    si_id: int,
    org_id: int | None = None,
) -> OrganizationEntity:
    valid_fields = OrganizationEntity.__table__.columns.keys()
    data = {k: v for k, v in dto.model_dump().items() if k in valid_fields}
    data["si_id"] = si_id

    if org_id:
        # --- UPDATE ---
        org = (
            db.query(OrganizationEntity)
            .filter(OrganizationEntity.id == org_id, OrganizationEntity.si_id == si_id)
            .first()
        )
        if not org:
            raise ValueError(f"Organization {org_id} not found under SI {si_id}")
        for k, v in data.items():
            setattr(org, k, v)
        db.flush()
    else:
        # --- CREATE ---
        org = OrganizationEntity(**data)
        db.add(org)
        db.flush()

    return org


def update_org_disabled(db: Session, org_id: int, disabled: bool):
    q = select(OrganizationEntity).where(OrganizationEntity.id == org_id)
    result = db.execute(q)
    org = result.scalars().first()

    if not org:
        raise ValueError(f"Organization {org_id} not found")

    org.disabled = disabled
    db.commit()
    db.refresh(org)
    return org


def get_users_by_si_and_org(db: Session, si_id: int, org_id: int):
    UR = user_roles_table.alias("ur")

    stmt = (
        select(
            UserEntity.id.label("user_id"),
            UserEntity.name,
            UserEntity.email,
            UserEntity.picture,
            RoleEntity.id.label("role_id"),
            RoleEntity.name.label("role_name"),
            RoleEntity.description.label("role_desc"),
            ReportGroupSetEntity.id.label("report_group_set_id"),
            ReportGroupSetEntity.name.label("report_group_set_name"),
        )
        .select_from(UserEntity)
        .join(UR, UR.c.user_id == UserEntity.id)
        .outerjoin(RoleEntity, RoleEntity.id == UR.c.role_id)
        .outerjoin(
            UserReportGroupSetAccessEntity,
            UserReportGroupSetAccessEntity.user_id == UserEntity.id
        )
        .outerjoin(
            ReportGroupSetEntity,
            and_(
                ReportGroupSetEntity.id == UserReportGroupSetAccessEntity.report_group_set_id,
                ReportGroupSetEntity.org_id == org_id
            )
        )
        .where(
            or_(
                and_(UR.c.scope_type == "super", UR.c.scope_id == 0),
                and_(UR.c.scope_type == "si", UR.c.scope_id == si_id),
                and_(UR.c.scope_type == "org", UR.c.scope_id == org_id),
            )
        )
    )

    return db.execute(stmt).all()


def get_org_business_modules(db: Session, org_id: int) -> List[BusinessModuleItemDTO]:
    """獲取組織的 business_modules"""
    q = (
        select(
            BusinessModuleEntity.id,
            BusinessModuleEntity.name,
        )
        .select_from(org_business_modules)
        .join(
            BusinessModuleEntity,
            BusinessModuleEntity.id == org_business_modules.c.business_modules_id,
        )
        .where(org_business_modules.c.org_id == org_id)
    )
    rows = db.execute(q).all()
    return [BusinessModuleItemDTO(id=row.id, name=row.name) for row in rows]
