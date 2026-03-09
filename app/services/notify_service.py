from app.decorators.external_api import external_api
from app.dtos.notify_dto import (
    AlertInfoResponseDTO,
    CreateAlertRequestDTO,
    CreateAlertResponseDTO,
    DeleteAlertResponseDTO,
    TriggerAlertResponseDTO,
)
from app.services.base_http_service import BaseHTTPService


class NotifyService(BaseHTTPService):

    def __init__(self):
        super().__init__(
            base_url_env="NOTIFY_API_URL",
            default_base_url="http://localhost:9000",
        )

    @external_api("notify_api")
    async def get_alert_info(
        self, org_id: int, limit: int, page: int, token: str
    ) -> AlertInfoResponseDTO:
        data = await self.get(
            path=f"org/{org_id}/alert/info",
            params={"limit": limit, "page": page},
            token=token,
        )
        return AlertInfoResponseDTO(**data)

    @external_api("notify_api")
    async def create_alert(
        self, org_id: int, body: CreateAlertRequestDTO, token: str
    ) -> CreateAlertResponseDTO:
        data = await self.post(
            path=f"org/{org_id}/alert/create",
            payload=body.model_dump(exclude_none=True),
            token=token,
        )
        return CreateAlertResponseDTO(**data)

    @external_api("notify_api")
    async def delete_alert(
        self, org_id: int, alert_id: int, token: str
    ) -> DeleteAlertResponseDTO:
        data = await self.delete(
            path=f"org/{org_id}/alert/delete",
            payload={"id": alert_id},
            token=token,
        )
        return DeleteAlertResponseDTO(**data)

    @external_api("notify_api")
    async def trigger_alert(self, token: str) -> TriggerAlertResponseDTO:
        data = await self.post(
            path="schedule/job/alert/start",
            payload={},
            token=token,
        )
        return TriggerAlertResponseDTO(**data)


notify_service = NotifyService()
