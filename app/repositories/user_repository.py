from sqlalchemy import and_, case, literal, select
from sqlalchemy.orm import Session, aliased
from app.entities.organization_entity import OrganizationEntity
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.si_entity import SIEntity
from app.entities.user_entity import UserEntity
from app.dtos.user_dto import UserCreateDTO
from app.entities.associations_entity import (
    user_roles as user_roles_table,
)


def get_all_users(db: Session):
    return db.query(UserEntity).all()


def create_user(db: Session, user: UserCreateDTO):
    db_user = UserEntity(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(UserEntity).filter(UserEntity.email == email).first()


def get_user(db: Session, user_id: int):
    return db.scalar(select(UserEntity).where(UserEntity.id == user_id))


def get_organizations_by_si_id(db: Session, si_id: int):
    return (
        db.execute(select(OrganizationEntity).where(OrganizationEntity.si_id == si_id))
        .scalars()
        .all()
    )


def get_user_roles(db: Session, user_id: int):
    return db.execute(
        select(
            user_roles_table.c.scope_type,
            user_roles_table.c.scope_id,
            user_roles_table.c.role_id,
            user_roles_table.c.isActive,
        ).where(user_roles_table.c.user_id == user_id)
    ).all()


def get_si_all(db: Session):
    return db.execute(select(SIEntity)).scalars().all()


def get_si_user_roles(db: Session, user_id: int):
    q = (
        select(
            SIEntity.id,
            SIEntity.name,
            SIEntity.logo,
            SIEntity.disabled,
            SIEntity.created_at,
            SIEntity.updated_at,
        )
        .select_from(user_roles_table)
        .join(
            SIEntity,
            and_(
                user_roles_table.c.scope_type == literal("si"),
                SIEntity.id == user_roles_table.c.scope_id,
            ),
        )
        .where(user_roles_table.c.user_id == user_id)
    )
    rows = db.execute(q).mappings().all()
    return rows


def get_user_roles_si_org_perm(db: Session, user_id: int):
    SI_scope = aliased(SIEntity, name="si_scope")
    SI_of_org = aliased(SIEntity, name="si_of_org")

    q = (
        select(
            user_roles_table.c.scope_type,
            user_roles_table.c.scope_id,
            user_roles_table.c.role_id,
            user_roles_table.c.isActive,
            case(
                (user_roles_table.c.scope_type == literal("si"), SI_scope.id),
                else_=SI_of_org.id,
            ).label("si_id"),
            case(
                (user_roles_table.c.scope_type == literal("si"), SI_scope.name),
                else_=SI_of_org.name,
            ).label("si_name"),
            OrganizationEntity.id.label("org_id"),
            OrganizationEntity.name.label("org_name"),
            OrganizationEntity.logo.label("org_logo"),
            SI_scope.logo.label("si_logo"),
            RoleEntity.name.label("role_name"),
            PermissionEntity.name.label("perm_name"),
            PermissionEntity.type.label("perm_type"),
        )
        .join(RoleEntity, RoleEntity.id == user_roles_table.c.role_id)
        .join(RoleEntity.permissions)
        # scope_type = 'si' → 直接用 scope_id 對 si
        .outerjoin(
            SI_scope,
            and_(
                user_roles_table.c.scope_type == literal("si"),
                SI_scope.id == user_roles_table.c.scope_id,
            ),
        )
        # scope_type = 'org' → 先對 org.id = scope_id
        .outerjoin(
            OrganizationEntity,
            and_(
                user_roles_table.c.scope_type == literal("org"),
                OrganizationEntity.id == user_roles_table.c.scope_id,
            ),
        )
        # 再把 org.si_id 連到另一個 si 別名
        .outerjoin(
            SI_of_org,
            and_(
                user_roles_table.c.scope_type == literal("org"),
                OrganizationEntity.si_id == SI_of_org.id,
            ),
        )
        .where(user_roles_table.c.user_id == user_id)
    )
    rows = db.execute(q).all()
    return rows


def get_permissions(db: Session):
    return db.execute(select(PermissionEntity.name, PermissionEntity.type)).all()


def get_all_orgs(db: Session):
    return db.execute(
        select(
            OrganizationEntity.id,
            OrganizationEntity.name,
            OrganizationEntity.si_id,
            OrganizationEntity.logo,
        )
    ).all()


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
