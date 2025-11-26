from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.services import user_service
from app.dtos.user_dto import (
    UserAccessTreeResponseDTO,
    UserCreateDTO,
    UserReadDTO,
)
from typing import List
from app.services.jwt_service import token_required


router = APIRouter(prefix="/user", tags=["User"])


@router.get("", response_model=List[UserReadDTO])
@router_try()
def get_users(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return user_service.get_users(db)


@router.post("", response_model=UserReadDTO)
@router_try()
def create_user(
    user: UserCreateDTO,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    return user_service.add_user(db, user)


@router.get("/info_access", response_model=UserAccessTreeResponseDTO)
@router_try()
def get_user_access_tree(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> UserAccessTreeResponseDTO:
    """
    Get current user access tree
    """
    return user_service.get_user_access_tree(db, user_info)
