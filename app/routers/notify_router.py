from fastapi import APIRouter, Depends, Request
from app.decorators import router_try
from app.dtos.notify_dto import (
    AlertInfoResponseDTO,
    CreateAlertRequestDTO,
    CreateAlertResponseDTO,
    DeleteAlertResponseDTO,
    TriggerAlertResponseDTO,
)
from app.services.jwt_service import token_required
from app.services.notify_service import notify_service

router = APIRouter(prefix="/notify", tags=["Notify"])


@router.get(
    "/org/{org_id}/alert",
    response_model=AlertInfoResponseDTO,
)
@router_try()
async def get_alert_info(
    org_id: int,
    request: Request,
    limit: int = 10,
    page: int = 1,
    _=Depends(token_required),
) -> AlertInfoResponseDTO:
    """Get alert info list for an organization"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.get_alert_info(org_id, limit, page, token)


@router.post(
    "/org/{org_id}/alert",
    response_model=CreateAlertResponseDTO,
)
@router_try()
async def create_alert(
    org_id: int,
    body: CreateAlertRequestDTO,
    request: Request,
    _=Depends(token_required),
) -> CreateAlertResponseDTO:
    """Create a new alert schedule for an organization"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.create_alert(org_id, body, token)


@router.delete(
    "/org/{org_id}/alert/{alert_id}",
    response_model=DeleteAlertResponseDTO,
)
@router_try()
async def delete_alert(
    org_id: int,
    alert_id: int,
    request: Request,
    _=Depends(token_required),
) -> DeleteAlertResponseDTO:
    """Delete an alert schedule for an organization"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.delete_alert(org_id, alert_id, token)


@router.post(
    "/schedule/job/alert/start",
    response_model=TriggerAlertResponseDTO,
)
@router_try()
async def trigger_alert(
    request: Request,
    _=Depends(token_required),
) -> TriggerAlertResponseDTO:
    """Trigger all scheduled alerts"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return await notify_service.trigger_alert(token)
