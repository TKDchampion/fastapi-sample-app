from collections import defaultdict
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import user_service
from app.dtos.user_dto import UserAccessTreeResponseDTO, UserCreateDTO, UserReadDTO
from typing import List
from app.services.jwt_service import token_required

# TODO: 待移除
from sqlalchemy import select
from app.entities.associations_entity import user_roles as user_roles_table
from app.entities.organization_entity import OrganizationEntity
from app.entities.si_entity import SIEntity
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.user_entity import UserEntity


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/user", tags=["User"])


@router.get("", response_model=List[UserReadDTO])
def get_users(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return user_service.get_users(db)


@router.post("", response_model=UserReadDTO)
def create_user(
    user: UserCreateDTO,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return user_service.add_user(db, user)


@router.get("/info_access", response_model=UserAccessTreeResponseDTO)
def get_user_access_tree(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> UserAccessTreeResponseDTO:
    """
    Refactored:
    - ~3–6 SQL queries total, regardless of graph size
    - No per-row .scalar() calls
    - All joins batched
    """
    try:
        return user_service.build_for_user(db, user_info.id)
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail={"type": "error", "msg": e.detail.get("msg", "Unknown error")},
        )


@router.get("/info_access", response_model=UserAccessTreeResponseDTO)
def get_user_access_tree(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> UserAccessTreeResponseDTO:
    """
    Refactored:
    - ~3–6 SQL queries total, regardless of graph size
    - No per-row .scalar() calls
    - All joins batched
    """
    try:
        return user_service.build_for_user(db, user_info.id)
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail={"type": "error", "msg": e.detail.get("msg", "Unknown error")},
        )


@router.get("/{user_id}")
def get_user_access_tree(user_id: int, db: Session = Depends(get_db)):
    # Step 1. 查 user 是否存在
    user = db.scalar(select(UserEntity).where(UserEntity.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Step 2. 查 user 的所有 roles (含 scope)
    user_roles = (
        db.execute(
            select(user_roles_table).where(user_roles_table.c.user_id == user_id)
        )
        .mappings()
        .all()
    )
    permissions_all = db.execute(
        select(PermissionEntity.name, PermissionEntity.type)
    ).all()

    perms_by_type = defaultdict(list)
    for name, type in permissions_all:
        perms_by_type[type].append(name)

    result = {
        "level": "super",
        "isActive": False,
        "permissions": [],
        "accessibleNode": [],
    }

    # Step 3. super 層級
    has_super = any(ur.scope_type == "super" for ur in user_roles)

    if has_super:
        result["isActive"] = True
        result["permissions"] = perms_by_type["super"]

        si_list = db.scalars(select(SIEntity)).all()

        for si_obj in si_list:
            orgs = db.scalars(
                select(OrganizationEntity).where(OrganizationEntity.si_id == si_obj.id)
            ).all()

            org_nodes = [
                {
                    "level": "org",
                    "id": org.id,
                    "name": org.name,
                    "role": "owner",
                    "isActive": True,
                    "permissions": perms_by_type["org"],
                }
                for org in orgs
            ]

            result["accessibleNode"].append(
                {
                    "level": "si",
                    "id": si_obj.id,
                    "name": si_obj.name,
                    "isActive": True,
                    "permissions": perms_by_type["si"],
                    "accessibleNode": org_nodes,
                }
            )

        return result  # super user 完成

    # Step 4. 處理 SI 層級
    si_roles = [ur for ur in user_roles if ur.scope_type == "si"]
    si_map = {}

    for ur in si_roles:
        si_obj = db.scalar(select(SIEntity).where(SIEntity.id == ur.scope_id))
        if not si_obj:
            continue

        si_map[si_obj.id] = {
            "level": "si",
            "id": si_obj.id,
            "name": si_obj.name,
            "isActive": ur.isActive if ur.isActive is not None else False,
            "role": "owner",
            "permissions": perms_by_type["si"],  # SI 全權限
            "accessibleNode": [],  # orgs later fill
        }

    # Step 5. 處理 Org 層級
    org_roles = [ur for ur in user_roles if ur.scope_type == "org"]

    for ur in org_roles:
        org_obj = db.scalar(
            select(OrganizationEntity).where(OrganizationEntity.id == ur.scope_id)
        )
        if not org_obj:
            continue

        si_obj = db.scalar(select(SIEntity).where(SIEntity.id == org_obj.si_id))

        # 查 Org role 名稱
        role_obj = db.scalar(select(RoleEntity).where(RoleEntity.id == ur.role_id))

        # 查 Org 角色的權限
        permission_rows = db.execute(
            select(PermissionEntity.name)
            .join(RoleEntity.permissions)
            .where(RoleEntity.id == ur.role_id)
        ).all()
        org_permissions = [r[0] for r in permission_rows]

        # 若此 SI 已存在於 si_map → SI 覆蓋 ORG（全部 org full perm）
        if si_obj.id in si_map:
            # 這個 org 也要進 accessibleNode
            si_map[si_obj.id]["accessibleNode"].append(
                {
                    "level": "org",
                    "id": org_obj.id,
                    "name": org_obj.name,
                    "role": "owner",  # 因 SI override
                    "isActive": True,
                    "permissions": perms_by_type["org"],  # full org perm
                }
            )
            continue

        # 如果沒有 SI 權限 → 只擁有個別 ORG 權限
        if si_obj.id not in si_map:
            si_map[si_obj.id] = {
                "level": "si",
                "id": si_obj.id,
                "name": si_obj.name,
                "isActive": False,  # SI 沒權限
                "role": None,
                "permissions": [],
                "accessibleNode": [],
            }

        si_map[si_obj.id]["accessibleNode"].append(
            {
                "level": "org",
                "id": org_obj.id,
                "name": org_obj.name,
                "role": role_obj.name,
                "isActive": ur.isActive if ur.isActive is not None else False,
                "permissions": org_permissions,
            }
        )

    # Step 6. SI 權限 → 自動補齊所有 org (避免漏 org)
    for si_id, si_entry in si_map.items():
        if si_entry["permissions"] != perms_by_type["si"]:
            continue  # skip: 不是 SI 權限

        orgs = db.scalars(
            select(OrganizationEntity).where(OrganizationEntity.si_id == si_id)
        ).all()

        # 既有 org ids
        existing_org_ids = {o["id"] for o in si_entry["accessibleNode"]}

        for org in orgs:
            if org.id not in existing_org_ids:
                si_entry["accessibleNode"].append(
                    {
                        "level": "org",
                        "id": org.id,
                        "name": org.name,
                        "role": "owner",
                        "isActive": True,
                        "permissions": perms_by_type["org"],  # full org perms
                    }
                )

    # Step 7. 排序 (optional)
    result["accessibleNode"] = list(si_map.values())

    return {"user": UserReadDTO.model_validate(user), "permissionTree": result}
