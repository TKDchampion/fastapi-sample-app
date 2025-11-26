from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.dtos.si_dto import SIListResponseDTO
from app.services import si_service
from app.dtos.user_dto import (
    UserReadDTO,
)
from app.services.jwt_service import token_required


router = APIRouter(prefix="/si", tags=["SI"])


@router.get("/list", response_model=SIListResponseDTO)
@router_try()
def get_user_si(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> SIListResponseDTO:
    """
    Get current user SI
    """
    return si_service.get_user_si(db, user_info.id)
