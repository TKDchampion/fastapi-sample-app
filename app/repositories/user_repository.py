from datetime import datetime, timezone
from sqlalchemy import and_, case, literal, select, or_, exists, func
from sqlalchemy.orm import Session, aliased
from app.entities.organization_entity import OrganizationEntity
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.si_entity import SIEntity
from app.entities.user_entity import UserEntity
from app.dtos.user_dto import UserCreateDTO
from app.entities.associations_entity import (
    user_roles as user_roles_table,
    role_permissions as role_permissions_table,
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


def get_user_by_id(db: Session, user_id: int):
    return db.scalar(select(UserEntity).where(UserEntity.id == user_id))


def get_user_roles(db: Session, user_id: int):
    return db.execute(
        select(
            user_roles_table.c.scope_type,
            user_roles_table.c.scope_id,
            user_roles_table.c.role_id,
        ).where(user_roles_table.c.user_id == user_id)
    ).all()


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
            OrganizationEntity.disabled.label("org_disabled"),
            OrganizationEntity.contract_start.label("org_contract_start"),
            OrganizationEntity.contract_end.label("org_contract_end"),
            SI_scope.logo.label("si_logo"),
            RoleEntity.name.label("role_name"),
            PermissionEntity.name.label("perm_name"),
            PermissionEntity.key.label("perm_key"),
            PermissionEntity.type.label("perm_type"),
        )
        .outerjoin(RoleEntity, RoleEntity.id == user_roles_table.c.role_id)
        .outerjoin(
            role_permissions_table,
            role_permissions_table.c.role_id == RoleEntity.id,
        )
        .outerjoin(
            PermissionEntity,
            PermissionEntity.id == role_permissions_table.c.permission_id,
        )
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


def check_user_has_permission_fast(
    db: Session,
    user_id: int,
    si_id: int,
    org_id: int | None = None,
    required_perm: str = "",
) -> bool:
    """
    精確權限查詢：快速檢查用戶是否對特定 si/org 有權限
    避免建立完整權限樹，適用於單個資源的權限驗證

    使用單一 SQL 查詢，通過 OR 條件組合所有可能的權限路徑：
    1. Super user
    2. SI level access
    3. Org level access (with/without specific permission)

    參數：
        user_id: 用戶 ID
        si_id: Service Instance ID
        org_id: Organization ID (可選)
        required_perm: 需要的權限 key，如果是 "pass" 則跳過權限檢查

    返回：
        True 如果用戶有權限，否則 False
    """
    now = func.now()

    # 情況 1: 只檢查 SI 層級 (沒有指定 org_id)
    if org_id is None:
        subq = (
            select(literal(1))
            .select_from(user_roles_table)
            .outerjoin(
                SIEntity,
                and_(
                    SIEntity.id == user_roles_table.c.scope_id,
                    user_roles_table.c.scope_type == "si",
                ),
            )
            .where(
                and_(
                    user_roles_table.c.user_id == user_id,
                    or_(
                        # Super user
                        user_roles_table.c.scope_type == "super",
                        # SI user
                        and_(
                            user_roles_table.c.scope_type == "si",
                            user_roles_table.c.scope_id == si_id,
                            SIEntity.disabled == False,
                        ),
                    ),
                )
            )
        )
        return db.scalar(select(exists(subq)))

    # 情況 2: 檢查 Org 層級權限 (有指定 org_id)
    # 構建統一的查詢，涵蓋所有可能的權限路徑
    if required_perm == "pass":
        # "pass" 模式：只要用戶有訪問權限即可，不檢查特定權限
        subq = (
            select(literal(1))
            .select_from(user_roles_table)
            .outerjoin(
                SIEntity,
                and_(
                    SIEntity.id == user_roles_table.c.scope_id,
                    user_roles_table.c.scope_type == "si",
                ),
            )
            .outerjoin(
                OrganizationEntity,
                or_(
                    # SI 層級：join org 來驗證 org 存在且有效
                    and_(
                        user_roles_table.c.scope_type == "si",
                        OrganizationEntity.si_id == SIEntity.id,
                        OrganizationEntity.id == org_id,
                    ),
                    # Org 層級：直接 join
                    and_(
                        user_roles_table.c.scope_type == "org",
                        OrganizationEntity.id == user_roles_table.c.scope_id,
                    ),
                ),
            )
            .where(
                and_(
                    user_roles_table.c.user_id == user_id,
                    or_(
                        # 路徑 1: Super user
                        user_roles_table.c.scope_type == "super",
                        # 路徑 2: SI user 訪問該 SI 下的 org
                        and_(
                            user_roles_table.c.scope_type == "si",
                            SIEntity.id == si_id,
                            SIEntity.disabled == False,
                            OrganizationEntity.id == org_id,
                            OrganizationEntity.disabled == False,
                            OrganizationEntity.contract_start <= now,
                            OrganizationEntity.contract_end >= now,
                        ),
                        # 路徑 3: Org user 直接訪問該 org
                        and_(
                            user_roles_table.c.scope_type == "org",
                            OrganizationEntity.id == org_id,
                            OrganizationEntity.si_id == si_id,
                            OrganizationEntity.disabled == False,
                            OrganizationEntity.contract_start <= now,
                            OrganizationEntity.contract_end >= now,
                        ),
                    ),
                )
            )
        )
    else:
        # 需要特定權限：只有 Super 或 Org 層級的特定權限可以通過
        # (SI 層級用戶也可以訪問，但不需要特定權限)
        subq = (
            select(literal(1))
            .select_from(user_roles_table)
            .outerjoin(
                SIEntity,
                and_(
                    SIEntity.id == user_roles_table.c.scope_id,
                    user_roles_table.c.scope_type == "si",
                ),
            )
            .outerjoin(
                OrganizationEntity,
                or_(
                    # SI 層級
                    and_(
                        user_roles_table.c.scope_type == "si",
                        OrganizationEntity.si_id == SIEntity.id,
                        OrganizationEntity.id == org_id,
                    ),
                    # Org 層級
                    and_(
                        user_roles_table.c.scope_type == "org",
                        OrganizationEntity.id == user_roles_table.c.scope_id,
                    ),
                ),
            )
            .outerjoin(RoleEntity, RoleEntity.id == user_roles_table.c.role_id)
            .outerjoin(
                role_permissions_table,
                role_permissions_table.c.role_id == RoleEntity.id,
            )
            .outerjoin(
                PermissionEntity,
                PermissionEntity.id == role_permissions_table.c.permission_id,
            )
            .where(
                and_(
                    user_roles_table.c.user_id == user_id,
                    or_(
                        # 路徑 1: Super user
                        user_roles_table.c.scope_type == "super",
                        # 路徑 2: SI user（SI 用戶對 org 有完全訪問權限）
                        and_(
                            user_roles_table.c.scope_type == "si",
                            SIEntity.id == si_id,
                            SIEntity.disabled == False,
                            OrganizationEntity.id == org_id,
                            OrganizationEntity.disabled == False,
                            OrganizationEntity.contract_start <= now,
                            OrganizationEntity.contract_end >= now,
                        ),
                        # 路徑 3: Org user 有特定權限
                        and_(
                            user_roles_table.c.scope_type == "org",
                            OrganizationEntity.id == org_id,
                            OrganizationEntity.si_id == si_id,
                            OrganizationEntity.disabled == False,
                            OrganizationEntity.contract_start <= now,
                            OrganizationEntity.contract_end >= now,
                            PermissionEntity.key == required_perm,
                        ),
                    ),
                )
            )
        )

    return db.scalar(select(exists(subq)))
