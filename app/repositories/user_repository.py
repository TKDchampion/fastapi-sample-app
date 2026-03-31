from typing import List
from sqlalchemy import and_, case, literal, select, or_, exists, func, delete
from sqlalchemy.orm import Session, aliased
from app.entities.organization_entity import OrganizationEntity
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.si_entity import SIEntity
from app.entities.user_entity import UserEntity
from app.entities.user_report_group_set_access_entity import (
    UserReportGroupSetAccessEntity,
)
from app.entities.report_group_set_entity import ReportGroupSetEntity
from app.entities.report_group_entity import ReportGroupEntity
from app.dtos.user_dto import UserCreateDTO
from app.dtos.report_dto import (
    UserReportGroupItemDTO,
    SidebarReportGroupSetItemDTO,
    SidebarReportGroupItemDTO,
)
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


def get_report_group_sets_by_ids_and_org(
    db: Session, group_set_ids: List[int], org_id: int
) -> List[ReportGroupSetEntity]:
    """驗證 group_set_ids 是否都屬於該 org"""
    return db.scalars(
        select(ReportGroupSetEntity).where(
            and_(
                ReportGroupSetEntity.id.in_(group_set_ids),
                ReportGroupSetEntity.org_id == org_id,
            )
        )
    ).all()


def replace_user_report_group_set_accesses(
    db: Session, user_id: int, org_id: int, group_set_ids: List[int]
) -> None:
    """刪除該 user 在指定 org 的 report_group_set_accesses，並批量新增新的"""
    # 找出該 org 下所有 group_set_id 的子查詢
    subquery = select(ReportGroupSetEntity.id).where(
        ReportGroupSetEntity.org_id == org_id
    )
    # 刪除該 user + org 的現有 accesses
    db.execute(
        delete(UserReportGroupSetAccessEntity).where(
            and_(
                UserReportGroupSetAccessEntity.user_id == user_id,
                UserReportGroupSetAccessEntity.report_group_set_id.in_(subquery),
            )
        )
    )

    # 批量新增新的 accesses
    if group_set_ids:
        for group_set_id in group_set_ids:
            access = UserReportGroupSetAccessEntity(
                user_id=user_id,
                report_group_set_id=group_set_id,
            )
            db.add(access)


def get_user_business_permission_keys(
    db: Session, user_id: int, si_id: int, org_id: int
) -> set[str] | None:
    """
    獲取用戶在特定 org 下的 business permission keys
    - Super user: 返回 None 表示有所有權限
    - SI user: 返回 None 表示有所有權限
    - Org user: 返回 business.{key} 中的 key 集合

    返回：
        set[str] 包含 business module keys（例如 "advertising", "retention"）
        如果是 None 則表示有所有權限（super/si user）
    """
    # 先檢查是否為 super 或 si user
    scope_check = db.execute(
        select(user_roles_table.c.scope_type, user_roles_table.c.scope_id).where(
            user_roles_table.c.user_id == user_id
        )
    ).all()

    for row in scope_check:
        if row.scope_type == "super":
            return None  # Super user 有所有權限
        if row.scope_type == "si" and row.scope_id == si_id:
            return None  # SI user 對該 SI 下的 org 有所有權限

    # Org user: 查詢 business 權限
    q = (
        select(PermissionEntity.key)
        .select_from(user_roles_table)
        .join(RoleEntity, RoleEntity.id == user_roles_table.c.role_id)
        .join(role_permissions_table, role_permissions_table.c.role_id == RoleEntity.id)
        .join(
            PermissionEntity,
            PermissionEntity.id == role_permissions_table.c.permission_id,
        )
        .where(
            and_(
                user_roles_table.c.user_id == user_id,
                user_roles_table.c.scope_type == "org",
                user_roles_table.c.scope_id == org_id,
                PermissionEntity.key.like("business.%"),
            )
        )
    )
    rows = db.execute(q).all()

    # 提取 "business." 後面的 key
    return {row.key.split(".")[1] for row in rows if len(row.key.split(".")) > 1}


def get_user_report_groups_grouped(
    db: Session, user_id: int, org_id: int
) -> List[SidebarReportGroupSetItemDTO]:
    """
    獲取用戶在特定組織下可訪問的所有 report_groups，按 report_group_set 分組
    通過 user_report_group_set_accesses -> report_group_sets -> report_groups 連接
    report_groups 按 report_group.order 排序
    """
    q = (
        select(
            ReportGroupSetEntity.id.label("report_group_set_id"),
            ReportGroupEntity.id.label("report_group_id"),
            ReportGroupEntity.name.label("report_group_name"),
            ReportGroupEntity.order,
            ReportGroupEntity.logo.label("report_group_logo"),
        )
        .select_from(UserReportGroupSetAccessEntity)
        .join(
            ReportGroupSetEntity,
            ReportGroupSetEntity.id
            == UserReportGroupSetAccessEntity.report_group_set_id,
        )
        .join(
            ReportGroupEntity,
            ReportGroupEntity.report_group_set_id == ReportGroupSetEntity.id,
        )
        .where(
            and_(
                UserReportGroupSetAccessEntity.user_id == user_id,
                ReportGroupSetEntity.org_id == org_id,
            )
        )
        .order_by(ReportGroupSetEntity.id, ReportGroupEntity.order)
    )
    rows = db.execute(q).all()

    # Group by report_group_set_id
    grouped: dict[int, List[SidebarReportGroupItemDTO]] = {}
    for row in rows:
        set_id = row.report_group_set_id
        if set_id not in grouped:
            grouped[set_id] = []
        grouped[set_id].append(
            SidebarReportGroupItemDTO(
                report_group_id=row.report_group_id,
                report_group_name=row.report_group_name,
                report_group_logo=row.report_group_logo,
            )
        )

    return [
        SidebarReportGroupSetItemDTO(
            report_groups_sets_id=set_id,
            report_groups=report_groups,
        )
        for set_id, report_groups in grouped.items()
    ]
