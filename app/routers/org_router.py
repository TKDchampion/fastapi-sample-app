import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.org_dto import OrgListResponseDTO
from app.services import org_service
from app.dtos.user_dto import (
    UserReadDTO,
)
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/org", tags=["Org"])


@router.get("/list/{si_id}", response_model=OrgListResponseDTO)
def get_organizations_by_si_id(
    si_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> OrgListResponseDTO:
    """
    Get organizations by SI ID
    """
    try:
        return org_service.get_organizations_by_si_id(db, si_id)
    except HTTPException:
        # 已是 HTTPException，直接拋出
        raise
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "msg": "Unknown error"},
        )
