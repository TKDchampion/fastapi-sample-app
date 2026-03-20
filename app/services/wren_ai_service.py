import csv
import logging
import os
import tempfile
import uuid
from typing import AsyncIterator

logger = logging.getLogger(__name__)

import httpx
from fastapi.responses import FileResponse, JSONResponse
from app.decorators.external_api import external_api

from app.utils.validate_sqlstr import validate_sql
import json
from sqlalchemy.orm import Session
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.dtos.user_dto import UserReadDTO
from app.dtos.wren_ai_dto import (
    AskRequestDTO,
    ChatbotReadDTO,
    ChartRequestDTO,
    ChartResponseDTO,
    CreateMessageDTO,
    GenerateSQLRequestDTO,
    GenerateSQLResponseDTO,
    RunSQLRequestDTO,
    RunSQLResponseDTO,
)
from app.domain.exception.domain_exception import DomainException
from app.entities.message_entity import MessageContentType, MessageRole, MessageStatus
from app.repositories import chatbot_repository, message_repository, thread_repository
from app.services.base_http_service import BaseHTTPService
from app.services.permission_guard_service import verify_user_permission

from google.cloud import bigquery
import base64

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

    def get_chatbot(
        self, db: Session, user: UserReadDTO, si_id: int, org_id: int
    ) -> ChatbotReadDTO:
        chatbot = self._verify_and_get_chatbot(db, user, si_id, org_id)
        return ChatbotReadDTO(id=chatbot.id, name=chatbot.name)

    async def generate_sql(
        self, endpoint: str, req: GenerateSQLRequestDTO, db: Session, user: UserReadDTO
    ) -> GenerateSQLResponseDTO:
        chatbot = self._verify_and_get_chatbot(db, user, req.si_id, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            **({"threadId": req.threadId} if req.threadId else {}),
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
            **({"threadId": req.threadId} if req.threadId else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        return RunSQLResponseDTO(**data)

    def _extract_stream_as_json(self, buffer: bytes) -> list:
        events = []
        for line in buffer.split(b"\n"):
            if not line.startswith(b"data:"):
                continue
            try:
                data = json.loads(line[5:].strip())
                events.append(data)
            except Exception:
                pass
        return events

    def create_messages(
        self,
        db: Session,
        thread_id: uuid.UUID,
        user_msg: CreateMessageDTO,
        system_content_json: list,
    ) -> None:
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
        message_repository.create_message(
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
                    self.create_messages(db, thread_id, user_msg, stream_json)
            except Exception as e:
                logger.exception("CREATE_MESSAGES_ERROR: %s", e)

        return _stream()

    async def run_chart(
        self, endpoint: str, req: ChartRequestDTO, db: Session, user: UserReadDTO
    ) -> ChartResponseDTO:
        chatbot = self._verify_and_get_chatbot(db, user, req.si_id, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            "customInstruction": f"{req.customInstruction} chart",
            "sql": req.sql,
            **({"threadId": req.threadId} if req.threadId else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        return ChartResponseDTO(**data)

    async def download_table(self, query: str):
        count_query = f"SELECT COUNT(*) as total_rows FROM ({query})"
        count_result = client.query(count_query).result()
        total_rows = list(count_result)[0].total_rows
        limit = 10000
        if total_rows > limit:
            return JSONResponse(
                content={
                    "message": "The query returns too many rows to download (limit: 10,000).",
                    "total_rows": total_rows,
                },
                status_code=200,
            )

        validate_query = validate_sql(query, limit)
        result = client.query(validate_query).result()

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", mode="w", newline="", encoding="utf-8"
        ) as tmpfile:
            writer = csv.writer(tmpfile)
            writer.writerow([field.name for field in result.schema])
            for row in result:
                writer.writerow(list(row.values()))
            tmpfile_path = tmpfile.name

        return FileResponse(tmpfile_path, media_type="text/csv", filename="result.csv")
