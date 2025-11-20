from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.organization_entity import OrganizationEntity
from app.entities.si_entity import SIEntity


def get_si_all(db: Session):
    stmt = select(
        SIEntity.id,
        SIEntity.name,
        SIEntity.logo,
        SIEntity.disabled,
        SIEntity.created_at,
        SIEntity.updated_at,
    )

    return db.execute(stmt).mappings().all()


def get_si_org_tree(db: Session):
    stmt = (
        select(
            SIEntity.id.label("si_id"),
            SIEntity.name.label("si_name"),
            SIEntity.logo.label("si_logo"),
            OrganizationEntity.id.label("org_id"),
            OrganizationEntity.name.label("org_name"),
            OrganizationEntity.logo.label("org_logo"),
            OrganizationEntity.disabled.label("org_disabled"),
            OrganizationEntity.contract_start.label("org_contract_start"),
            OrganizationEntity.contract_end.label("org_contract_end"),
        )
        .join(OrganizationEntity, OrganizationEntity.si_id == SIEntity.id, isouter=True)
        .order_by(SIEntity.id)
    )
    return db.execute(stmt).mappings().all()
