import csv
import logging
import os
import tempfile
from typing import AsyncIterator

logger = logging.getLogger(__name__)

from fastapi.responses import FileResponse, JSONResponse

from app.utils.validate_sqlstr import validate_sql
import json
from sqlalchemy.orm import Session
from app.domain.access_tree.check_user_access import PermissionCheckParams
from app.dtos.user_dto import UserReadDTO
from app.dtos.wren_ai_dto import (
    AskRequestDTO,
    ChartRequestDTO,
    ChartResponseDTO,
    GenerateSQLRequestDTO,
    GenerateSQLResponseDTO,
    RunSQLRequestDTO,
    RunSQLResponseDTO,
)
from app.domain.exception.domain_exception import DomainException
from app.repositories import chatbot_repository
from app.services.base_http_service import BaseHTTPService
from app.services.permission_guard_service import verify_user_permission

from google.cloud import bigquery
import base64

raw = os.environ["BQ_SERVICE_ACCOUNT_KEY"]
decoded = base64.b64decode(raw).decode("utf-8")
info = json.loads(decoded)
client = bigquery.Client.from_service_account_info(info)


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
                msg=f"No chatbot found for org_id={org_id}",
                type="not_found",
                code=404,
            )
        return chatbot

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
        if req.threadId:
            payload["threadId"] = req.threadId

        async def _stream() -> AsyncIterator[bytes]:
            try:
                async for chunk in self.post_stream(
                    path=endpoint, payload=payload, token=chatbot.wren_key
                ):
                    yield chunk
            except Exception as e:
                # 這裡只處理串流中途錯誤
                logger.exception("ASK_STREAM_ERROR: %s", e)
                yield b"event: error\ndata: {}\n\n"
                return

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
