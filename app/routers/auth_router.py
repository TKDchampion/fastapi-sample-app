import logging
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from app.dtos.auth_dto import AuthLoginResponseDTO, GoogleAuthCodeDTO
from app.services.auth_service import AuthService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/google_login", response_model=AuthLoginResponseDTO)
async def google_login(
    request_dto: GoogleAuthCodeDTO,
    service: AuthService = Depends(AuthService),
):
    try:
        return await service.authenticate_with_code(request_dto.code)
    except Exception as e:
        logger.warning(f"AuthService failed: {e.detail}")
        detail = e.detail if isinstance(e.detail, dict) else {"msg": str(e.detail)}
        raise HTTPException(
            status_code=401,
            detail={
                "type": detail.get("type", "error"),
                "msg": detail.get("msg", "Unknown error"),
            },
        )
