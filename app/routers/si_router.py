import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import si_service
from app.dtos.user_dto import (
    UserReadDTO,
    UserSIListResponseDTO,
)
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/si", tags=["SI"])


@router.get("/list", response_model=UserSIListResponseDTO)
def get_user_si(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> UserSIListResponseDTO:
    """
    Get current user SI
    """
    try:
        return si_service.get_user_si(db, user_info.id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )
