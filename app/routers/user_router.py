import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import user_service
from app.dtos.user_dto import UserAccessTreeResponseDTO, UserCreateDTO, UserReadDTO
from typing import List
from app.services.jwt_service import token_required


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
    Refactored:
    - ~3–6 SQL queries total, regardless of graph size
    - No per-row .scalar() calls
    - All joins batched
    """
    try:
        return user_service.build_for_user(db, user_info.id)
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail={"type": "error", "msg": e.detail.get("msg", "Unknown error")},
        )
