from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.dtos.notify_dto import (
    AlertInfoResponseDTO,
    CreateAlertRequestDTO,
    CreateAlertResponseDTO,
    DeleteAlertResponseDTO,
    TriggerAlertResponseDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.services.jwt_service import token_required
from app.services.notify_service import notify_service

router = APIRouter(prefix="/notify", tags=["Notify"])


@router.get(
    "/si/{si_id}/org/{org_id}/alert",
    response_model=AlertInfoResponseDTO,
)
@router_try()
async def get_alert_info(
    si_id: int,
    org_id: int,
    request: Request,
    limit: int = 10,
    page: int = 1,
    user: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
) -> AlertInfoResponseDTO:
    """Get alert info list for an organization"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.get_alert_info(org_id, limit, page, token, db, user, si_id)


@router.post(
    "/si/{si_id}/org/{org_id}/alert",
    response_model=CreateAlertResponseDTO,
)
@router_try()
async def create_alert(
    si_id: int,
    org_id: int,
    body: CreateAlertRequestDTO,
    request: Request,
    user: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
) -> CreateAlertResponseDTO:
    """Create a new alert schedule for an organization"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.create_alert(org_id, body, token, db, user, si_id)


@router.delete(
    "/si/{si_id}/org/{org_id}/alert/{alert_id}",
    response_model=DeleteAlertResponseDTO,
)
@router_try()
async def delete_alert(
    si_id: int,
    org_id: int,
    alert_id: int,
    request: Request,
    user: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
) -> DeleteAlertResponseDTO:
    """Delete an alert schedule for an organization"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.delete_alert(org_id, alert_id, token, db, user, si_id)


@router.post(
    "/si/{si_id}/org/{org_id}/schedule/job/alert/start",
    response_model=TriggerAlertResponseDTO,
)
@router_try()
async def trigger_alert(
    si_id: int,
    org_id: int,
    request: Request,
    user: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
) -> TriggerAlertResponseDTO:
    """Trigger all scheduled alerts"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.trigger_alert(token, db, user, si_id, org_id)
