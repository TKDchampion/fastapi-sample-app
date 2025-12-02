from typing import List
from fastapi import APIRouter
from fastapi.params import Depends
from app.database import get_db
from app.decorators import router_try
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
def delete_user_role(
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
