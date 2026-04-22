from sqlalchemy.orm import Session
from app.decorators.external_api import external_api
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.dtos.notify_dto import (
    AlertInfoResponseDTO,
    CreateAlertRequestDTO,
    CreateAlertResponseDTO,
    DeleteAlertResponseDTO,
    SyncIngestionRequestDTO,
    SyncIngestionResponseDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.services.base_http_service import BaseHTTPService
from app.services.permission_guard_service import verify_user_permission


@external_api("notify_api")
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

    async def get_alert_info(
        self,
        org_id: int,
        limit: int,
        page: int,
        token: str,
        db: Session,
        user: UserReadDTO,
        si_id: int,
    ) -> AlertInfoResponseDTO:
        self._verify_notify_permission(db, user, si_id, org_id)
        data = await self.get(
            path=f"org/{org_id}/alert/info",
            params={"limit": limit, "page": page},
            token=token,
        )
        return AlertInfoResponseDTO(**data)

    async def create_alert(
        self,
        org_id: int,
        body: CreateAlertRequestDTO,
        token: str,
        db: Session,
        user: UserReadDTO,
        si_id: int,
    ) -> CreateAlertResponseDTO:
        self._verify_notify_permission(db, user, si_id, org_id)
        data = await self.post(
            path=f"org/{org_id}/alert/create",
            payload=body.model_dump(exclude_none=True),
            token=token,
        )
        return CreateAlertResponseDTO(**data)

    async def delete_alert(
        self,
        org_id: int,
        alert_id: int,
        token: str,
        db: Session,
        user: UserReadDTO,
        si_id: int,
    ) -> DeleteAlertResponseDTO:
        self._verify_notify_permission(db, user, si_id, org_id)
        data = await self.delete(
            path=f"org/{org_id}/alert/delete",
            payload={"id": alert_id},
            token=token,
        )
        return DeleteAlertResponseDTO(**data)

    async def sync_ingestion(
        self,
        org_id: int,
        body: SyncIngestionRequestDTO,
        token: str,
    ) -> SyncIngestionResponseDTO:
        data = await self.post(
            path=f"org/{org_id}/ingestion/sync",
            payload=body.model_dump(),
            token=token,
        )
        return SyncIngestionResponseDTO(**data)


notify_service = NotifyService()
