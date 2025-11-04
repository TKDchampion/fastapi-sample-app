from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import user_service
from app.dtos.user_dto import UserAccessTreeResponseDTO, UserCreateDTO, UserReadDTO
from typing import List

# TODO: 待移除
from sqlalchemy import select
from app.entities.associations_entity import user_roles as user_roles_table
from app.entities.organization_entity import OrganizationEntity
from app.entities.si_entity import SIEntity
from app.entities.permission_entity import PermissionEntity
from app.entities.role_entity import RoleEntity
from app.entities.user_entity import UserEntity

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserReadDTO])
def get_users(db: Session = Depends(get_db)):
    return user_service.get_users(db)


@router.post("", response_model=UserReadDTO)
def create_user(user: UserCreateDTO, db: Session = Depends(get_db)):
    return user_service.add_user(db, user)


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

    result = {"level": "super", "isActive": False, "accessibleNode": []}

    # Step 3. super 層級
    has_super = any(ur.scope_type == "super" for ur in user_roles)
    permissions_all = db.scalars(
        select(PermissionEntity.name).where(PermissionEntity.name != None)
    ).all()

    if has_super:
        result["isActive"] = True

        si_list = db.scalars(select(SIEntity)).all()
        permissions = permissions_all
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
                    "permissions": permissions,
                }
                for org in orgs
            ]

            result["accessibleNode"].append(
                {
                    "level": "si",
                    "id": si_obj.id,
                    "name": si_obj.name,
                    "isActive": True,
                    "accessibleNode": org_nodes,
                }
            )

        return result  # super user 完成

    # Step 4. 處理 SI 層級
    si_roles = [ur for ur in user_roles if ur.scope_type == "si"]
    si_map = {}

    # 先紀錄有哪些 SI 層級
    si_ids_with_admin = set()

    for ur in si_roles:
        si_obj = db.scalar(select(SIEntity).where(SIEntity.id == ur.scope_id))
        if not si_obj:
            continue

        si_ids_with_admin.add(si_obj.id)

        si_entry = si_map.get(
            si_obj.id,
            {
                "level": "si",
                "id": si_obj.id,
                "name": si_obj.name,
                "isActive": True,
                "accessibleNode": [],
            },
        )
        si_map[si_obj.id] = si_entry

    # Step 5. 處理 Org 層級
    org_roles = [ur for ur in user_roles if ur.scope_type == "org"]

    for ur in org_roles:
        org_obj = db.scalar(
            select(OrganizationEntity).where(OrganizationEntity.id == ur.scope_id)
        )
        role_obj = db.scalar(select(RoleEntity).where(RoleEntity.id == ur.role_id))
        si_obj = db.scalar(select(SIEntity).where(SIEntity.id == org_obj.si_id))

        # 查角色權限
        permission_rows = db.execute(
            select(PermissionEntity.name)
            .join(RoleEntity.permissions)
            .where(RoleEntity.id == ur.role_id)
        )
        permissions = [r[0] for r in permission_rows]

        # 若該 org 所屬 si 已經在 si_ids_with_admin，則 override 成 all
        if si_obj.id in si_ids_with_admin:
            permissions = permissions_all

        # 加入對應 SI node
        if si_obj.id not in si_map:
            si_map[si_obj.id] = {
                "level": "si",
                "id": si_obj.id,
                "name": si_obj.name,
                "isActive": False,
                "accessibleNode": [],
            }

        si_map[si_obj.id]["accessibleNode"].append(
            {
                "level": "org",
                "id": org_obj.id,
                "name": org_obj.name,
                "role": role_obj.name,
                "isActive": ur.isActiveOrg if ur.isActiveOrg is not None else False,
                "permissions": permissions,
            }
        )

    # Step 6. 把有 SI 權限的全部 org 一起補進來
    for si_id in si_ids_with_admin:
        orgs = db.scalars(
            select(OrganizationEntity).where(OrganizationEntity.si_id == si_id)
        ).all()
        si_entry = si_map.get(si_id)
        if not si_entry:
            si_obj = db.scalar(select(SIEntity).where(SIEntity.id == si_id))
            si_entry = {
                "level": "si",
                "id": si_obj.id,
                "name": si_obj.name,
                "isActive": True,
                "accessibleNode": [],
            }
            si_map[si_id] = si_entry

        existing_org_ids = {org_node["id"] for org_node in si_entry["accessibleNode"]}
        for org in orgs:
            if org.id not in existing_org_ids:
                si_entry["accessibleNode"].append(
                    {
                        "level": "org",
                        "id": org.id,
                        "name": org.name,
                        "role": "owner",
                        "isActive": True,
                        "permissions": permissions_all,
                    }
                )

    # Step 7. 整合結果
    result["accessibleNode"] = list(si_map.values())

    return UserAccessTreeResponseDTO(
        user=UserReadDTO.model_validate(user), permissionInfo=result
    )
