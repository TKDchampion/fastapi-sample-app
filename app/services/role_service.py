from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.domain.access_tree.check_user_access import OrgWriteParams
from app.dtos.role_dto import AssignRoleParamDTO
from app.dtos.user_dto import UserReadDTO
from app.repositories import role_repository
from app.services import user_service
from app.services.permission_guard_service import verify_org_write_permission


def assign_role_to_user(db: Session, param: AssignRoleParamDTO, user_info: UserReadDTO):
    try:
        params = OrgWriteParams(
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
    except Exception as e:
        db.rollback()
        print("🔥 EXCEPTION:", e)
        raise HTTPException(
            500,
            detail={"type": "error", "msg": "create user role error"},
        )
