from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.dtos.org_dto import OrgUpsertRequestDTO
from app.entities.organization_entity import OrganizationEntity
from app.entities.associations_entity import (
    user_roles as user_roles_table,
)


def get_orgs_by_si_id(db: Session, si_id: int):
    return (
        db.execute(select(OrganizationEntity).where(OrganizationEntity.si_id == si_id))
        .scalars()
        .all()
    )


def get_orgs_ids_by_si(db: Session, si_id: int, ids: list[int]):
    return (
        db.execute(
            select(OrganizationEntity).where(
                OrganizationEntity.si_id == si_id,
                OrganizationEntity.id.in_(ids),
            )
        )
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


def upsert_org(
    db: Session,
    dto: OrgUpsertRequestDTO,
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


def update_user_role_is_active(
    db: Session, user_id: int, org_id: int, new_is_active: bool
):
    stmt = (
        update(user_roles_table)
        .where(
            user_roles_table.c.user_id == user_id,
            user_roles_table.c.scope_type == "org",
            user_roles_table.c.scope_id == org_id,
        )
        .values(isActive=new_is_active)
    )
    result = db.execute(stmt)
    db.commit()

    return result.rowcount
