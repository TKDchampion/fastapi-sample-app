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


@router.get("/{user_id}", response_model=UserAccessTreeResponseDTO)
def get_user_access_tree(
    user_id: int, db: Session = Depends(get_db)
) -> UserAccessTreeResponseDTO:
    """
    Refactored:
    - ~3–6 SQL queries total, regardless of graph size
    - No per-row .scalar() calls
    - All joins batched
    """
    return user_service.build_for_user(db, user_id)
