from sqlalchemy.orm import Session
from app.decorators.external_api import external_api
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.dtos.notify_dto import (
    AlertInfoResponseDTO,
    CreateAlertRequestDTO,
    CreateAlertResponseDTO,
    DeleteAlertResponseDTO,
    TriggerAlertResponseDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.services.base_http_service import BaseHTTPService
from app.services.permission_guard_service import verify_user_permission


class NotifyService(BaseHTTPService):

    def __init__(self):
        super().__init__(
            base_url_env="NOTIFY_API_URL",
            default_base_url="http://localhost:9000",
        )

    def _verify_notify_permission(
        self, db: Session, user: UserReadDTO, si_id: int, org_id: int
    ):
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.notify"),
        )

    @external_api("notify_api")
    async def get_alert_info(
        self, org_id: int, limit: int, page: int, token: str, db: Session, user: UserReadDTO, si_id: int
    ) -> AlertInfoResponseDTO:
        self._verify_notify_permission(db, user, si_id, org_id)
        data = await self.get(
            path=f"org/{org_id}/alert/info",
            params={"limit": limit, "page": page},
            token=token,
        )
        return AlertInfoResponseDTO(**data)

    @external_api("notify_api")
    async def create_alert(
        self, org_id: int, body: CreateAlertRequestDTO, token: str, db: Session, user: UserReadDTO, si_id: int
    ) -> CreateAlertResponseDTO:
        self._verify_notify_permission(db, user, si_id, org_id)
        data = await self.post(
            path=f"org/{org_id}/alert/create",
            payload=body.model_dump(exclude_none=True),
            token=token,
        )
        return CreateAlertResponseDTO(**data)

    @external_api("notify_api")
    async def delete_alert(
        self, org_id: int, alert_id: int, token: str, db: Session, user: UserReadDTO, si_id: int
    ) -> DeleteAlertResponseDTO:
        self._verify_notify_permission(db, user, si_id, org_id)
        data = await self.delete(
            path=f"org/{org_id}/alert/delete",
            payload={"id": alert_id},
            token=token,
        )
        return DeleteAlertResponseDTO(**data)

    @external_api("notify_api")
    async def trigger_alert(
        self, token: str, db: Session, user: UserReadDTO, si_id: int, org_id: int
    ) -> TriggerAlertResponseDTO:
        self._verify_notify_permission(db, user, si_id, org_id)
        data = await self.post(
            path="schedule/job/alert/start",
            payload={},
            token=token,
        )
        return TriggerAlertResponseDTO(**data)


notify_service = NotifyService()
