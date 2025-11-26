import logging
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from requests import Session
from app.database import get_db
from app.dtos.role_dto import AssignRoleParamDTO, RoleDTO, UserRoleCreateDTO
from app.dtos.user_dto import UserReadDTO
from app.services import role_service
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)
role_router = APIRouter(prefix="/role", tags=["Role"])
si_router = APIRouter(prefix="/si", tags=["Role"])
org_router = APIRouter(prefix="/org", tags=["Role"])


@si_router.post("/{si_id}/{org_id}/create_user")
def create_user_role(
    user_role: UserRoleCreateDTO,
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    try:
        param = AssignRoleParamDTO(
            email=user_role.email,
            role_id=user_role.role_id,
            si_id=si_id,
            org_id=org_id,
        )
        return role_service.assign_role_to_user(db, param, user_info)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        print("🔥 EXCEPTION:", e)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "create user role error"},
        )


@org_router.get("/{org_id}/roles", response_model=list[RoleDTO])
def get_roles_by_org(
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """
    Get all roles belonging to an organization.
    """
    try:
        return role_service.roles_by_org(db, org_id)

    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )
