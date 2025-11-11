from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.organization_entity import OrganizationEntity
from app.entities.si_entity import SIEntity


def get_si_all(db: Session):
    return db.execute(select(SIEntity)).scalars().all()


def get_si_org_tree(db: Session):
    stmt = (
        select(
            SIEntity.id,
            SIEntity.name,
            SIEntity.logo,
            OrganizationEntity.id,
            OrganizationEntity.name,
            OrganizationEntity.logo,
        )
        .join(OrganizationEntity, OrganizationEntity.si_id == SIEntity.id, isouter=True)
        .order_by(SIEntity.id)
    )
    return db.execute(stmt).all()
