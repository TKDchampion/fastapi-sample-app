from typing import List
from fastapi import APIRouter
from fastapi.params import Depends
from app.database import get_db
from app.decorators import router_try
from app.dtos.permission_dto import OrgPermissionDTO, RolePermissionUpdateDTO
from app.dtos.role_dto import (
    RolePermissionDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.services import permission_service
from app.services.jwt_service import token_required
from sqlalchemy.orm import Session


perm_router = APIRouter(prefix="/permission", tags=["Permission"])
si_router = APIRouter(prefix="/si", tags=["Permission"])


@si_router.get(
    "/{si_id}/org/{org_id}/role_permissions", response_model=List[RolePermissionDTO]
)
@router_try()
def get_role_permissions(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return permission_service.get_role_permissions(
        db=db,
        si_id=si_id,
        org_id=org_id,
        user_info=user_info,
    )


@perm_router.get("/org/{org_id}", response_model=List[OrgPermissionDTO])
@router_try()
def list_org_permissions(
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return permission_service.get_all_permissions_org(db, org_id)


@si_router.put(
    "/{si_id}/org/{org_id}/role_permissions", response_model=List[RolePermissionDTO]
)
@router_try()
def update_role_permissions(
    si_id: int,
    org_id: int,
    role_permissions: List[RolePermissionUpdateDTO],
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return permission_service.update_role_permissions(
        db=db,
        si_id=si_id,
        org_id=org_id,
        role_permissions=role_permissions,
        user_info=user_info,
    )
