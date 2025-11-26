from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.domain.access_tree.check_user_access import OrgWriteParamsDTO
from app.dtos.role_dto import AssignRoleParamDTO
from app.dtos.user_dto import UserReadDTO
from app.repositories import role_repository, user_repository
from app.services import user_service
from app.services.permission_guard_service import verify_org_write_permission


def assign_role_to_user(db: Session, param: AssignRoleParamDTO, user_info: UserReadDTO):
    try:
        params = OrgWriteParamsDTO(
            si_id=param.si_id, org_id=param.org_id, perm="member.edit"
        )
        verify_org_write_permission(db, user_info, params)

        # 1. Validate user
        user = user_service.get_user_by_email(db, param.email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"msg": "User not found", "type": "user not found"},
            )

        # 2. Validate role belongs to org
        role = role_repository.role_belongs_to_org(db, param.role_id, param.org_id)
        if not role:
            raise HTTPException(
                status_code=404,
                detail={"msg": "Role not found", "type": "role not found"},
            )

        # 3. Insert into user_roles
        new_user_role = role_repository.create_user_role(
            db, param.org_id, param.role_id, user.id
        )

        result = {
            "msg": "Role assigned",
            "user_id": user.id,
            "role_id": param.role_id,
            "org_id": param.org_id,
            "data": new_user_role._mapping,
        }

        # 4. Commit
        db.commit()
        return result

    except HTTPException:
        db.rollback()
        raise


def roles_by_org(db: Session, org_id: int):
    try:
        return role_repository.roles_by_org(db, org_id)
    except HTTPException:
        raise


def update_user_role(
    db: Session,
    si_id: int,
    org_id: int,
    user_id: int,
    role_id: int,
    user_info: UserReadDTO,
):
    try:
        # 1. Permission check
        params = OrgWriteParamsDTO(si_id=si_id, org_id=org_id, perm="member.edit")
        verify_org_write_permission(db, user_info, params)

        # 2. Validate user exists
        user = user_repository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"msg": "User not found", "type": "user_not_found"},
            )

        # 3. Validate role belongs to this org
        role = role_repository.role_belongs_to_org(db, role_id, org_id)
        if not role:
            raise HTTPException(
                status_code=404,
                detail={"msg": "Role not found in this org", "type": "role_not_found"},
            )

        # 4. Validate user_roles row exists for this org
        user_role = role_repository.get_user_role(db, user_id, org_id)
        if not user_role:
            raise HTTPException(
                status_code=404,
                detail={
                    "msg": "User has no role in this org",
                    "type": "user_role_not_found",
                },
            )

        # 5. Update role_id
        updated = role_repository.update_user_role(
            db=db,
            user_id=user_id,
            org_id=org_id,
            role_id=role_id,
        )

        res = {
            "msg": "Role updated",
            "user_id": user_id,
            "org_id": org_id,
            "role_id": role_id,
            "data": updated._mapping,
        }

        db.commit()

        return res

    except HTTPException:
        db.rollback()
        raise
