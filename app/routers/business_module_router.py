from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.dtos.business_module_dto import BusinessModuleDTO
from app.dtos.user_dto import UserReadDTO
from app.services import business_module_service
from app.services.jwt_service import token_required


router = APIRouter(prefix="/business_module", tags=["Business_module"])


@router.get("/list", response_model=List[BusinessModuleDTO])
@router_try()
def get_business_module(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """
    Get current user SI
    """
    return business_module_service.get_business_module(db)
