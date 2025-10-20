import logging
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from app.dtos.auth_dto import AuthLoginRequestDTO, AuthLoginResponseDTO
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=AuthLoginResponseDTO)
async def login(
    request_dto: AuthLoginRequestDTO,
    service: AuthService = Depends(AuthService),
):
    try:
        return await service.verify_google_token(request_dto.access_token)
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise
