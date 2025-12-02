from typing import List
from fastapi import APIRouter
from fastapi.params import Depends
from app.database import get_db
from app.decorators import router_try
from app.dtos.role_dto import (
    AssignRoleParamDTO,
    RoleDTO,
    RolePermissionDTO,
    UserRoleCreateDTO,
)
from app.dtos.user_dto import UserReadDTO, UserRolesResponseDTO
from app.services import org_service, role_service
from app.services.jwt_service import token_required
from sqlalchemy.orm import Session


role_router = APIRouter(prefix="/role", tags=["Role"])
si_router = APIRouter(prefix="/si", tags=["Role"])
org_router = APIRouter(prefix="/org", tags=["Role"])


@si_router.get("/{si_id}/org/{org_id}/users", response_model=list[UserRolesResponseDTO])
@router_try()
def get_users_by_si_and_org(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """Get organization users"""

    return org_service.get_users_by_si_and_org(db, si_id, org_id, user_info)


@si_router.post("/{si_id}/org/{org_id}/create_user")
@router_try()
def create_user_role(
    user_role: UserRoleCreateDTO,
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    param = AssignRoleParamDTO(
        email=user_role.email,
        role_id=user_role.role_id,
        si_id=si_id,
        org_id=org_id,
    )
    return role_service.assign_role_to_user(db, param, user_info)


@org_router.get("/{org_id}/roles", response_model=list[RoleDTO])
@router_try()
def get_roles_by_org(
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """
    Get all roles belonging to an organization.
    """
    return role_service.roles_by_org(db, org_id)


@si_router.put("/{si_id}/org/{org_id}/user/{user_id}/role")
@router_try()
def update_user_role(
    si_id: int,
    org_id: int,
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return role_service.update_user_role(db, si_id, org_id, user_id, role_id, user_info)


@si_router.delete("/{si_id}/orgs/{org_id}/users/{user_id}/role")
@router_try()
def delete_user_role(
    si_id: int,
    org_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return role_service.delete_user_role(
        db=db,
        si_id=si_id,
        org_id=org_id,
        user_id=user_id,
        user_info=user_info,
    )
