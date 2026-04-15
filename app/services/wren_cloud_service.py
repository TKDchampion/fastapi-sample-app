import os

from app.decorators.external_api import external_api
from app.dtos.wren_ai_dto import WrenCloudKeyResponseDTO, WrenCloudProjectResponseDTO
from app.services.base_http_service import BaseHTTPService


@external_api("wren_cloud")
class WrenCloudService(BaseHTTPService):
    def __init__(self):
        super().__init__(
            base_url_env="WREN_CLOUD_URL",
            default_base_url="https://cloud.getwren.ai",
            timeout=30,
        )
        self._token = os.getenv("WREN_TOKEN", "")
        self._wren_org_id = os.getenv("WREN_ORG_ID", "")
        self._app_env = os.getenv("APP_ENV", "development")

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def display_name(self, org_id: int) -> str:
        prefix = "prod" if self._app_env == "production" else "dev"
        return f"{prefix}_{org_id}"

    async def create_project(self, org_id: int) -> WrenCloudProjectResponseDTO:
        payload = {
            "orgId": self._wren_org_id,
            "displayName": self.display_name(org_id),
            "language": "zh-TW",
            "timezone": "Asia/Taipei",
        }
        result = await self.post(
            path="/api/v1/projects",
            payload=payload,
            extra_headers=self._auth_headers(),
        )
        return WrenCloudProjectResponseDTO(**result)

    async def create_api_key(
        self, project_id: int | str, org_id: int
    ) -> WrenCloudKeyResponseDTO:
        payload = {"name": self.display_name(org_id)}
        result = await self.post(
            path=f"/api/v1/projects/{project_id}/keys",
            payload=payload,
            extra_headers=self._auth_headers(),
        )
        return WrenCloudKeyResponseDTO(**result)
