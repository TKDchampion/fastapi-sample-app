import csv
import logging
import os
import tempfile
import uuid
from typing import AsyncIterator, List, Optional
from fastapi import UploadFile

logger = logging.getLogger(__name__)

from fastapi.responses import FileResponse, JSONResponse
from app.decorators.external_api import external_api

from app.utils.validate_sqlstr import validate_sql
import json
from sqlalchemy.orm import Session
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.dtos.user_dto import UserReadDTO
from app.dtos.wren_ai_dto import (
    ArtifactReadDTO,
    ArtifactSummaryDTO,
    AskRequestDTO,
    ChatbotCsvReadDTO,
    CsvUploadResponseDTO,
    ChatbotReadDTO,
    ChartRequestDTO,
    ChartResponseDTO,
    CreateMessageDTO,
    GenerateSQLRequestDTO,
    GenerateSQLResponseDTO,
    MessageListResponseDTO,
    MessagePageDTO,
    MessageReadDTO,
    RunSQLRequestDTO,
    RunSQLResponseDTO,
    ThreadListResponseDTO,
    ThreadPageDTO,
    ThreadReadDTO,
    ThreadSummaryDTO,
    UpsertModelResponseDTO,
    WrenCloudKeyResponseDTO,
    WrenCloudProjectResponseDTO,
    WrenSetupResponseDTO,
)
from app.domain.exception.domain_exception import DomainException
from app.entities.artifact_entity import ArtifactType
from app.entities.message_entity import MessageContentType, MessageRole, MessageStatus
from app.repositories import (
    artifact_repository,
    chatbot_csv_repository,
    chatbot_repository,
    message_repository,
    thread_repository,
)
from app.services.base_http_service import BaseHTTPService
from app.dtos.notify_dto import SyncIngestionRequestDTO, SyncIngestionTableInfoDTO
from app.services.gcs_uploader import download_csv_templates_from_gcs, upload_csv_to_gcs
from app.services.permission_guard_service import verify_user_permission

from google.cloud import bigquery
import base64


def _to_gs_uri(https_url: str) -> str:
    """Convert https://storage.googleapis.com/{bucket}/{blob} to gs://{bucket}/{blob}."""
    prefix = "https://storage.googleapis.com/"
    if https_url.startswith(prefix):
        return "gs://" + https_url[len(prefix) :]
    return https_url


raw = os.environ["BQ_SERVICE_ACCOUNT_KEY"]
decoded = base64.b64decode(raw).decode("utf-8")
info = json.loads(decoded)
client = bigquery.Client.from_service_account_info(info)


@external_api("wren_ai")
class WrenAiService(BaseHTTPService):

    def __init__(self):
        super().__init__(
            base_url_env="WREN_API_URL",
            default_base_url="http://localhost:8000",
            timeout=6000,
        )
        self._cloud_token = os.getenv("WREN_TOKEN", "")
        self._wren_org_id = os.getenv("WREN_ORG_ID", "")
        self._app_env = os.getenv("APP_ENV", "development")
        self._cloud_base_url = os.getenv("WREN_CLOUD_URL", "https://cloud.getwren.ai")

    def _cloud_auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._cloud_token}"}

    def _cloud_display_name(self, org_id: int) -> str:
        prefix = "prod" if self._app_env == "production" else "dev"
        return f"{prefix}_{org_id}"

    async def _create_wren_project(self, org_id: int):
        payload = {
            "orgId": self._wren_org_id,
            "displayName": self._cloud_display_name(org_id),
            "language": "ZH_TW",
            "timezone": "Asia/Taipei",
        }
        result = await self.post(
            path="/api/v1/projects",
            payload=payload,
            extra_headers=self._cloud_auth_headers(),
            override_base_url=self._cloud_base_url,
        )
        return WrenCloudProjectResponseDTO(**result)

    async def _create_wren_api_key(self, project_id: int | str, org_id: int):
        payload = {"name": self._cloud_display_name(org_id)}
        result = await self.post(
            path=f"/api/v1/projects/{project_id}/keys",
            payload=payload,
            extra_headers=self._cloud_auth_headers(),
            override_base_url=self._cloud_base_url,
        )
        return WrenCloudKeyResponseDTO(**result)

    def _verify_and_get_chatbot(
        self, db: Session, user: UserReadDTO, si_id: int, org_id: int
    ):
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.chatbot"),
        )
        chatbot = chatbot_repository.get_chatbot_by_org_id(db, org_id)
        if not chatbot:
            raise DomainException(
                msg="Organization missing chatbot configuration",
                type="chatbot_mapping_missing",
                code=400,
            )
        return chatbot

    def get_threads(
        self,
        db: Session,
        user: UserReadDTO,
        si_id: int,
        org_id: int,
        user_id_filter: Optional[int],
        chatbot_id_filter: Optional[int],
        cursor: Optional[str],
        limit: int,
    ) -> ThreadListResponseDTO:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.chatbot"),
        )
        threads = thread_repository.get_threads(
            db, org_id, user_id_filter, chatbot_id_filter, cursor, limit
        )

        next_cursor = None
        if len(threads) == limit:
            last = threads[-1]
            raw = f"{last.last_message_at.isoformat() if last.last_message_at else ''}|{last.id}"
            next_cursor = base64.b64encode(raw.encode()).decode()

        items = [
            ThreadReadDTO(
                id=str(t.id),
                wren_ai_thread_id=t.wren_thread_id,
                org_id=t.org_id,
                user_id=t.user_id,
                chatbot_id=t.chatbot_id,
                title=t.title,
                last_message_at=t.last_message_at,
                message_count=t.message_count,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in threads
        ]
        return ThreadListResponseDTO(
            items=items, page=ThreadPageDTO(next_cursor=next_cursor)
        )

    def get_messages(
        self,
        db: Session,
        user: UserReadDTO,
        si_id: int,
        org_id: int,
        thread_id: uuid.UUID,
        cursor: Optional[str],
        limit: int,
        order: str,
    ) -> MessageListResponseDTO:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.chatbot"),
        )
        thread = thread_repository.get_thread_by_id(db, thread_id)
        if not thread or thread.org_id != org_id:
            raise DomainException(msg="Thread not found", type="not_found", code=404)

        cursor_seq = None
        if cursor:
            try:
                cursor_seq = int(base64.b64decode(cursor).decode())
            except Exception:
                pass

        messages = message_repository.get_messages(
            db, thread_id, cursor_seq, limit, order
        )

        next_cursor = None
        if len(messages) == limit:
            next_cursor = base64.b64encode(str(messages[-1].seq).encode()).decode()

        items = [
            MessageReadDTO(
                id=str(m.id),
                thread_id=str(m.thread_id),
                seq=m.seq,
                role=m.role.value,
                content_type=m.content_type.value,
                content_text=m.content_text,
                content_json=m.content_json,
                status=m.status.value,
                parent_message_id=(
                    str(m.parent_message_id) if m.parent_message_id else None
                ),
                created_at=m.created_at,
                artifacts=(
                    [
                        ArtifactSummaryDTO(
                            id=str(a.id),
                            message_id=str(a.message_id),
                            type=a.type.value,
                            title=a.title,
                        )
                        for a in m.artifacts
                    ]
                ),
            )
            for m in messages
        ]

        return MessageListResponseDTO(
            thread=ThreadSummaryDTO(
                id=str(thread.id),
                wren_thread_id=thread.wren_thread_id,
                title=thread.title,
            ),
            items=items,
            page=MessagePageDTO(next_cursor=next_cursor),
        )

    def get_artifact(
        self,
        db: Session,
        user: UserReadDTO,
        si_id: int,
        org_id: int,
        thread_id: uuid.UUID,
        message_id: uuid.UUID,
        artifact_id: uuid.UUID,
    ) -> ArtifactReadDTO:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.chatbot"),
        )
        thread = thread_repository.get_thread_by_id(db, thread_id)
        if not thread or thread.org_id != org_id:
            raise DomainException(msg="Thread not found", type="not_found", code=404)

        message = message_repository.get_message_by_thread_and_id(
            db, thread_id, message_id
        )
        if not message:
            raise DomainException(msg="Message not found", type="not_found", code=404)

        artifact = artifact_repository.get_artifact_by_id(db, artifact_id, message_id)
        if not artifact:
            raise DomainException(msg="Artifact not found", type="not_found", code=404)

        return ArtifactReadDTO(
            id=str(artifact.id),
            thread_id=str(artifact.thread_id),
            message_id=str(artifact.message_id),
            type=artifact.type.value,
            title=artifact.title,
            spec_json=artifact.spec_json,
            data_json=artifact.data_json,
            storage_url=artifact.storage_url,
            created_at=artifact.created_at,
        )

    def rename_thread(
        self,
        db: Session,
        user: UserReadDTO,
        si_id: int,
        org_id: int,
        thread_id: uuid.UUID,
        title: str,
    ) -> ThreadReadDTO:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.chatbot"),
        )
        thread = thread_repository.get_thread_by_id(db, thread_id)
        if not thread or thread.org_id != org_id:
            raise DomainException(msg="Thread not found", type="not_found", code=404)
        thread = thread_repository.rename_thread(db, thread_id, title)
        return ThreadReadDTO(
            id=str(thread.id),
            wren_ai_thread_id=thread.wren_thread_id,
            org_id=thread.org_id,
            user_id=thread.user_id,
            chatbot_id=thread.chatbot_id,
            title=thread.title,
            last_message_at=thread.last_message_at,
            message_count=thread.message_count,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
        )

    def delete_thread(
        self,
        db: Session,
        user: UserReadDTO,
        si_id: int,
        org_id: int,
        thread_id: uuid.UUID,
    ) -> None:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.chatbot"),
        )
        thread = thread_repository.get_thread_by_id(db, thread_id)
        if not thread or thread.org_id != org_id:
            raise DomainException(msg="Thread not found", type="not_found", code=404)
        thread_repository.delete_thread(db, thread_id)

    def get_chatbot(
        self, db: Session, user: UserReadDTO, si_id: int, org_id: int
    ) -> ChatbotReadDTO:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="pass"),
        )
        chatbot = chatbot_repository.get_chatbot_by_org_id(db, org_id)
        if not chatbot:
            raise DomainException(
                msg="WrenAI is not connected for this organization",
                type="wren_ai_not_connected",
                code=400,
            )
        return ChatbotReadDTO(id=chatbot.id, name=chatbot.name)

    def get_upload_csvs(
        self, db: Session, user: UserReadDTO, si_id: int, org_id: int
    ) -> List[ChatbotCsvReadDTO]:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(si_id=si_id, org_id=org_id, perm="business.chatbot"),
        )
        chatbot = chatbot_repository.get_chatbot_by_org_id(db, org_id)
        if not chatbot:
            raise DomainException(
                msg="此組織尚未串接 WrenAI，請聯繫管理員進行設定",
                type="wren_ai_not_connected",
                code=404,
            )
        records = chatbot_csv_repository.find_all_by_chatbot_id(db, chatbot.id)
        return [
            ChatbotCsvReadDTO(
                id=r.id,
                chatbot_id=r.chatbot_id,
                gcs_url=r.gcs_url,
                original_filename=r.original_filename,
                created_at=r.created_at,
                is_success=r.is_success,
            )
            for r in records
        ]

    async def generate_sql(
        self, endpoint: str, req: GenerateSQLRequestDTO, db: Session, user: UserReadDTO
    ) -> GenerateSQLResponseDTO:
        chatbot = self._verify_and_get_chatbot(db, user, req.si_id, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            **({"threadId": req.wren_ai_thread_id} if req.wren_ai_thread_id else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        return GenerateSQLResponseDTO(**data)

    async def run_sql(
        self, endpoint: str, req: RunSQLRequestDTO, db: Session, user: UserReadDTO
    ) -> RunSQLResponseDTO:
        chatbot = self._verify_and_get_chatbot(db, user, req.si_id, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "sql": req.sql,
            **({"threadId": req.wren_ai_thread_id} if req.wren_ai_thread_id else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        result = RunSQLResponseDTO(**data)

        if req.thread_id and req.message_id:
            self.create_artifact(
                db=db,
                thread_id=uuid.UUID(req.thread_id),
                message_id=uuid.UUID(req.message_id),
                type="table",
                title=req.title,
                data_json=result.model_dump(),
            )

        return result

    def _extract_stream_as_json(self, buffer: bytes) -> str:
        return buffer.decode("utf-8")

    def create_messages(
        self,
        db: Session,
        thread_id: uuid.UUID,
        user_msg: CreateMessageDTO,
        system_content_json: str,
    ) -> uuid.UUID:
        parent_id = (
            uuid.UUID(user_msg.parent_message_id)
            if user_msg.parent_message_id
            else None
        )
        next_seq = message_repository.get_next_seq(db, thread_id)

        user_message = message_repository.create_message(
            db=db,
            thread_id=thread_id,
            seq=next_seq,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            content_text=user_msg.content_text,
            content_json=None,
            status=MessageStatus.final,
            parent_message_id=parent_id,
        )
        system_message = message_repository.create_message(
            db=db,
            thread_id=thread_id,
            seq=next_seq + 1,
            role=MessageRole.system,
            content_type=MessageContentType.json,
            content_text=None,
            content_json=system_content_json,
            status=MessageStatus.final,
            parent_message_id=user_message.id,
        )
        db.commit()
        thread_repository.update_thread_stats(db, thread_id, message_count_increment=2)
        return system_message.id

    def _create_thread_from_chunk(
        self, buffer: bytes, db: Session, user: UserReadDTO, chatbot, req: AskRequestDTO
    ):
        for line in buffer.split(b"\n"):
            if not line.startswith(b"data:"):
                continue
            try:
                data = json.loads(line[5:].strip())
                if data.get("type") == "message_stop":
                    wren_thread_id = data.get("data", {}).get("threadId")
                    if wren_thread_id:
                        return thread_repository.create_thread(
                            db=db,
                            wren_thread_id=wren_thread_id,
                            org_id=req.org_id,
                            user_id=user.id,
                            chatbot_id=chatbot.id,
                            title=req.title,
                        )
            except Exception:
                pass
        return None

    async def ask(
        self, endpoint: str, req: AskRequestDTO, db: Session, user: UserReadDTO
    ) -> AsyncIterator[bytes]:
        # 驗證在 generator 外執行，確保錯誤在 response 開始前拋出
        chatbot = self._verify_and_get_chatbot(db, user, req.si_id, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            "returnBothSqlDialect": True,
        }
        if req.wren_ai_thread_id:
            payload["threadId"] = req.wren_ai_thread_id

        is_new_thread = req.thread_id is None

        async def _stream() -> AsyncIterator[bytes]:
            buffer = b""
            thread_created = False
            thread = None
            try:
                async for chunk in self.post_stream(
                    path=endpoint, payload=payload, token=chatbot.wren_key
                ):
                    yield chunk
                    buffer += chunk
                    if is_new_thread and not thread_created:
                        thread = self._create_thread_from_chunk(
                            buffer, db, user, chatbot, req
                        )
                        if thread:
                            thread_created = True
                            system_thread_id = str(thread.id)
                            yield (
                                f'data: {{"type": "thread_created", "data": {{"system_thread_id": "{system_thread_id}"}}}}\n\n'
                            ).encode()
            except Exception as e:
                # 這裡只處理串流中途錯誤
                logger.exception("ASK_STREAM_ERROR: %s", e)
                yield b"event: error\ndata: {}\n\n"
                return

            try:
                thread_id = (
                    thread.id
                    if thread
                    else (uuid.UUID(req.thread_id) if req.thread_id else None)
                )
                if thread_id:
                    stream_json = self._extract_stream_as_json(buffer)
                    user_msg = CreateMessageDTO(
                        role="user",
                        content_type="text",
                        content_text=req.question,
                        content_json=None,
                        status="final",
                        parent_message_id=None,
                    )
                    message_id = self.create_messages(
                        db, thread_id, user_msg, stream_json
                    )
                    yield (
                        f'data: {{"type": "message_created", "data": {{"message_id": "{message_id}"}}}}\n\n'
                    ).encode()
            except Exception as e:
                logger.exception("CREATE_MESSAGES_ERROR: %s", e)

        return _stream()

    def create_artifact(
        self,
        db: Session,
        thread_id: uuid.UUID,
        message_id: uuid.UUID,
        type: str,
        title: str,
        data_json: list | None,
        spec_json: dict | None = None,
        storage_url: str | None = None,
    ):
        message = message_repository.get_message_by_thread_and_id(
            db, thread_id, message_id
        )
        if not message:
            raise DomainException(
                msg="Message not found in thread",
                type="message_not_found",
                code=404,
            )
        return artifact_repository.create_artifact(
            db=db,
            thread_id=thread_id,
            message_id=message_id,
            type=ArtifactType(type),
            title=title,
            data_json=data_json,
            spec_json=spec_json,
            storage_url=storage_url,
        )

    async def run_chart(
        self, endpoint: str, req: ChartRequestDTO, db: Session, user: UserReadDTO
    ) -> ChartResponseDTO:
        chatbot = self._verify_and_get_chatbot(db, user, req.si_id, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            "customInstruction": f"{req.customInstruction} chart",
            "sql": req.sql,
            **({"threadId": req.wren_ai_thread_id} if req.wren_ai_thread_id else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        result = ChartResponseDTO(**data)

        if req.thread_id and req.message_id:
            self.create_artifact(
                db=db,
                thread_id=uuid.UUID(req.thread_id),
                message_id=uuid.UUID(req.message_id),
                type=req.customInstruction,
                title=req.title,
                data_json=result.model_dump(),
            )

        return result

    def upload_csv(
        self,
        db: Session,
        user: UserReadDTO,
        si_id: int,
        org_id: int,
        file: UploadFile,
    ) -> CsvUploadResponseDTO:
        chatbot = self._verify_and_get_chatbot(db, user, si_id, org_id)
        gcs_url = upload_csv_to_gcs(file)
        chatbot_csv_repository.create_csv_record(
            db=db,
            chatbot_id=chatbot.id,
            gcs_url=gcs_url,
            original_filename=file.filename,
        )
        db.commit()
        return CsvUploadResponseDTO(
            gcs_url=gcs_url,
            original_filename=file.filename,
        )

    def download_csv_template(
        self,
        db: Session,
        user: UserReadDTO,
        si_id: int,
        org_id: int,
        types: list,
    ) -> tuple:
        verify_user_permission(
            db,
            user,
            PermissionCheckParams(
                si_id=si_id, org_id=org_id, perm="org.permission.edit"
            ),
        )
        return download_csv_templates_from_gcs([t.value for t in types])

    async def download_table(self, query: str):
        limit = 10000
        normalized_query = query.strip().rstrip(";")

        safe_query = f"""
        SELECT *
        FROM ({normalized_query}) AS sub
        LIMIT {limit + 1}
        """

        result = client.query(safe_query).result()
        rows = list(result)

        if len(rows) > limit:
            return JSONResponse(
                content={
                    "message": f"The query returns too many rows to download (limit: {limit}).",
                    "total_rows": f">{limit}",
                },
                status_code=200,
            )

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", mode="w", newline="", encoding="utf-8"
        ) as tmpfile:
            writer = csv.writer(tmpfile)
            writer.writerow([field.name for field in result.schema])
            for row in rows:
                writer.writerow(list(row.values()))
            tmpfile_path = tmpfile.name

        return FileResponse(tmpfile_path, media_type="text/csv", filename="result.csv")

    async def upsert_model(
        self, db: Session, user: UserReadDTO, si_id: int, org_id: int, token: str
    ) -> UpsertModelResponseDTO:
        from app.services.notify_service import notify_service

        chatbot = self._verify_and_get_chatbot(db, user, si_id, org_id)
        csvs = chatbot_csv_repository.get_latest_failed_csvs_by_chatbot_id(db, chatbot.id)

        table_info = [
            SyncIngestionTableInfoDTO(
                table_name=os.path.splitext(csv.original_filename)[0],
                gcs_uri=_to_gs_uri(csv.gcs_url),
            )
            for csv in csvs
        ]

        body = SyncIngestionRequestDTO(
            table_info=table_info,
            models=chatbot.wren_models or [],
            project_name=chatbot.name,
        )

        print("SYNC_INGESTION_REQUEST_BODY:", body.json())

        result = await notify_service.sync_ingestion(org_id=org_id, body=body, token=token)

        # 成功：更新 chatbot.wren_models 與對應 CSV 的 is_success
        chatbot_repository.update_wren_models(
            db, chatbot.id, result.success_table_names
        )
        chatbot_csv_repository.mark_csvs_success(
            db, chatbot.id, set(result.success_table_names)
        )
        db.commit()

        return UpsertModelResponseDTO(**result.model_dump())

    async def setup_wren_for_org(
        self, db: Session, user: UserReadDTO, si_id: int, org_id: int
    ) -> WrenSetupResponseDTO:
        if chatbot_repository.get_chatbot_by_org_id(db, org_id):
            raise DomainException(
                msg="Chatbot already exists for this organization",
                type="chatbot_already_exists",
                code=409,
            )

        verify_user_permission(
            db,
            user,
            PermissionCheckParams(
                si_id=si_id, org_id=org_id, perm="org.permission.edit"
            ),
        )

        # 步驟一：建立 Wren Project
        project = await self._create_wren_project(org_id)

        # 步驟二：建立 API Key（前者成功才執行）
        api_key = await self._create_wren_api_key(project.project.id, org_id)

        # 步驟三：建立 chatbot 記錄
        chatbot, _ = chatbot_repository.upsert_chatbot(
            db,
            org_id=org_id,
            name=self._cloud_display_name(org_id),
            wren_project_id=str(project.project.id),
            wren_key=api_key.secret,
        )
        db.commit()

        return WrenSetupResponseDTO(
            id=chatbot.id,
            name=chatbot.name,
            org_id=chatbot.org_id,
            wren_project_id=chatbot.wren_project_id,
            wren_api_key=api_key.secret,
        )

    # async def download_table(self, query: str):
    #     count_query = f"SELECT COUNT(*) as total_rows FROM ({query})"
    #     count_result = client.query(count_query).result()
    #     total_rows = list(count_result)[0].total_rows
    #     limit = 10000
    #     if total_rows > limit:
    #         return JSONResponse(
    #             content={
    #                 "message": "The query returns too many rows to download (limit: 10,000).",
    #                 "total_rows": total_rows,
    #             },
    #             status_code=200,
    #         )

    #     validate_query = validate_sql(query, limit)
    #     result = client.query(validate_query).result()

    #     with tempfile.NamedTemporaryFile(
    #         delete=False, suffix=".csv", mode="w", newline="", encoding="utf-8"
    #     ) as tmpfile:
    #         writer = csv.writer(tmpfile)
    #         writer.writerow([field.name for field in result.schema])
    #         for row in result:
    #             writer.writerow(list(row.values()))
    #         tmpfile_path = tmpfile.name

    #     return FileResponse(tmpfile_path, media_type="text/csv", filename="result.csv")
