from fastapi import APIRouter
from fastapi.params import Depends
from app.decorators import router_try
from app.dtos.auth_dto import AuthLoginResponseDTO, GoogleAuthCodeDTO
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/google_login", response_model=AuthLoginResponseDTO)
@router_try()
async def google_login(
    request_dto: GoogleAuthCodeDTO,
    service: AuthService = Depends(AuthService),
):
    return await service.authenticate_with_code(request_dto)
