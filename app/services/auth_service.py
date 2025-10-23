import logging
import os
from fastapi import HTTPException
import httpx
from app.services import jwt_service
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
        self.token_base_url = "https://oauth2.googleapis.com"

    async def exchange_code_for_token(self, code: str) -> dict:
        data = {
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }
        try:
            return await self.post(
                path="token",
                payload=data,
                override_base_url=self.token_base_url,
                extra_headers={"content-type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "RequestError exchanging code for token: %s", exc, exc_info=True
            )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail={
                    "type": "invalid",
                    "msg": "Failed to exchange code for token",
                },
            )

    def prepare_request(self, payload: dict, headers: dict) -> tuple[dict, dict]:
        """
        Override BaseHTTPService.prepare_request for Google's x-www-form-urlencoded requirement.
        """
        if headers.get("content-type") == "application/x-www-form-urlencoded":
            return {"data": payload}, headers
        return super().prepare_request(payload, headers)

    async def google_auth(self, access_token: str) -> dict:
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
                status_code=exc.response.status_code,
                detail={
                    "type": "invalid",
                    "msg": "Invalid Google token",
                },
            )

    async def authenticate_with_code(self, code: str) -> dict:
        tokens = await self.exchange_code_for_token(code)
        user = await self.google_auth(tokens["access_token"])
        token = jwt_service.create_access_token(data={**user})

        return {**user, "token": token}
