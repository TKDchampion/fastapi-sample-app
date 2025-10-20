import logging
from fastapi import HTTPException
import httpx
from app.services.base_http_service import BaseHTTPService

logger = logging.getLogger(__name__)


class AuthService(BaseHTTPService):
    """
    A service for handling authentication-related HTTP requests.
    """

    def __init__(self):
        super().__init__(
            base_url_env="GOOGLE_API_BASE_URL",
            default_base_url="https://www.googleapis.com/oauth2/v3",
            timeout=10.0,
        )

    async def verify_google_token(self, access_token: str) -> dict:
        """
        Verify a Google access token and retrieve user information.
        """
        try:
            google_user = await self.post(
                path="userinfo", payload={}, token=access_token
            )
            return google_user
        except httpx.HTTPStatusError as exc:
            logger.error("RequestError calling google auth api: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=401,
                detail={
                    "type": "Invalid",
                    "msg": "Invalid Google token",
                },
            )
