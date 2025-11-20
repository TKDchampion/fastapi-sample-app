import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.business_module_dto import BusinessModuleDTO
from app.dtos.user_dto import UserReadDTO
from app.services import business_module_service
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/business_module", tags=["business_module"])


@router.get("/list", response_model=List[BusinessModuleDTO])
def get_business_module(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """
    Get current user SI
    """
    try:
        return business_module_service.get_business_module(db)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )
