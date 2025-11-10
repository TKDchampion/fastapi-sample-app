from collections import defaultdict
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, outerjoin
from app.database import get_db
from app.services import user_service
from app.dtos.user_dto import (
    UserAccessTreeResponseDTO,
    UserCreateDTO,
    UserReadDTO,
    UserSIListResponseDTO,
)
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
    Get current user access tree
    """
    try:
        return user_service.get_user_access_tree(db, user_info.id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )


@router.get("/{user_id}", response_model=UserAccessTreeResponseDTO)
def get_user_access_tree(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserAccessTreeResponseDTO:
    """
    test
    """
    try:
        return user_service.get_user_access_tree(db, user_id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )


@router.get("/si_list", response_model=UserSIListResponseDTO)
def get_user_si(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> UserSIListResponseDTO:
    """
    Get current user SI
    """
    try:
        return user_service.get_user_si(db, user_info.id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )
