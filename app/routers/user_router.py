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
from app.dtos.common_dto import TextResponseDTO
from app.dtos.report_dto import UserReportGroupItemDTO
from typing import List
from app.services.jwt_service import token_required


router = APIRouter(prefix="/user", tags=["User"])
si_router = APIRouter(prefix="/si", tags=["User"])


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


@si_router.put(
    "/{si_id}/org/{org_id}/user/{user_id}/report_group_sets",
    response_model=TextResponseDTO,
)
@router_try()
def set_user_report_group_sets(
    si_id: int,
    org_id: int,
    user_id: int,
    group_set_ids: List[int],
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> TextResponseDTO:
    """
    Set report group set accesses for a user.
    This will replace all existing accesses for the user.
    """
    return user_service.set_user_report_group_sets(
        db, si_id, org_id, user_id, group_set_ids, user_info
    )


@si_router.get(
    "/{si_id}/org/{org_id}/report_groups",
    response_model=List[UserReportGroupItemDTO],
)
@router_try()
def get_user_report_groups(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> List[UserReportGroupItemDTO]:
    """
    Get report groups accessible by the current user within a specific organization.
    Returns a list of report groups mapped from user's assigned report group sets, sorted by order.
    """
    return user_service.get_user_report_groups(db, si_id, org_id, user_info)
