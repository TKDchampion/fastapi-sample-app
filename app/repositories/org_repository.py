from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, noload, selectinload
from app.dtos.org_dto import OrgUpsertParamDTO
from app.entities.organization_entity import OrganizationEntity
from app.entities.associations_entity import (
    user_roles as user_roles_table,
)
from app.entities.role_entity import RoleEntity
from app.entities.user_entity import UserEntity


def get_orgs_by_sid(db: Session, si_id: int):
    return (
        db.execute(select(OrganizationEntity).where(OrganizationEntity.si_id == si_id))
        .scalars()
        .all()
    )


def get_orgs_by_sid_oids(db: Session, si_id: int, ids: list[int]):
    return (
        db.execute(
            select(OrganizationEntity)
            .options(
                noload(OrganizationEntity.business_modules),
                # selectinload(OrganizationEntity.business_modules)
            )
            .where(
                OrganizationEntity.si_id == si_id,
                OrganizationEntity.id.in_(ids),
            )
        )
        .scalars()
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


def get_by_name(db: Session, name: str) -> OrganizationEntity | None:
    stmt = select(OrganizationEntity).where(OrganizationEntity.name == name)
    result = db.execute(stmt)
    return result.scalars().first()


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
        )
        .select_from(UserEntity)
        .join(UR, UR.c.user_id == UserEntity.id)
        .outerjoin(RoleEntity, RoleEntity.id == UR.c.role_id)
        .where(
            or_(
                and_(UR.c.scope_type == "si", UR.c.scope_id == si_id),
                and_(UR.c.scope_type == "org", UR.c.scope_id == org_id),
            )
        )
    )

    return db.execute(stmt).all()
