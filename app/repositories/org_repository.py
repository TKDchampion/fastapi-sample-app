from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.organization_entity import OrganizationEntity


def get_organizations_by_si_id(db: Session, si_id: int):
    return (
        db.execute(select(OrganizationEntity).where(OrganizationEntity.si_id == si_id))
        .scalars()
        .all()
    )


def get_all_orgs(db: Session):
    return db.execute(
        select(
            OrganizationEntity.id,
            OrganizationEntity.name,
            OrganizationEntity.si_id,
            OrganizationEntity.logo,
        )
    ).all()
