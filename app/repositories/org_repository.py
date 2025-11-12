from sqlalchemy import select
from sqlalchemy.orm import Session
from app.dtos.org_dto import OrgCreateRequestDTO
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


def get_by_name(db: Session, name: str) -> OrganizationEntity | None:
    stmt = select(OrganizationEntity).where(OrganizationEntity.name == name)
    result = db.execute(stmt)
    return result.scalars().first()


def create_org(db: Session, dto: OrgCreateRequestDTO, si_id: int) -> OrganizationEntity:
    valid_fields = OrganizationEntity.__table__.columns.keys()
    data = {k: v for k, v in dto.model_dump().items() if k in valid_fields}
    data["si_id"] = si_id
    print("Creating organization with data:", data)
    org = OrganizationEntity(**data)
    db.add(org)
    db.flush()

    return org
