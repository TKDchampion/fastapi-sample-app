# import csv

# import os
# import tempfile
from typing import AsyncIterator

# from fastapi.responses import FileResponse, JSONResponse

# from flask import json
from sqlalchemy.orm import Session
from app.dtos.wren_ai_dto import (
    AskRequestDTO,
    ChartRequestDTO,
    ChartResponseDTO,
    GenerateSQLRequestDTO,
    GenerateSQLResponseDTO,
    RunSQLRequestDTO,
    RunSQLResponseDTO,
)
from app.repositories import chatbot_repository
from app.services.base_http_service import BaseHTTPService

# from app.utils.validate_sqlstr import validate_sql

# from google.cloud import bigquery
# import base64

# raw = os.environ["BQ_SERVICE_ACCOUNT_KEY"]
# decoded = base64.b64decode(raw).decode("utf-8")
# info = json.loads(decoded)
# client = bigquery.Client.from_service_account_info(info)


class WrenAiService(BaseHTTPService):

    def __init__(self):
        super().__init__(
            base_url_env="WREN_API_URL",
            default_base_url="http://localhost:8000",
            timeout=6000,
        )

    def _get_chatbot(self, db: Session, org_id: int):
        chatbot = chatbot_repository.get_chatbot_by_org_id(db, org_id)
        if not chatbot:
            raise ValueError(f"No chatbot found for org_id={org_id}")
        return chatbot

    async def generate_sql(
        self, endpoint: str, req: GenerateSQLRequestDTO, db: Session
    ) -> GenerateSQLResponseDTO:
        chatbot = self._get_chatbot(db, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            **({"threadId": req.threadId} if req.threadId else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        return GenerateSQLResponseDTO(**data)

    async def run_sql(
        self, endpoint: str, req: RunSQLRequestDTO, db: Session
    ) -> RunSQLResponseDTO:
        chatbot = self._get_chatbot(db, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "sql": req.sql,
            **({"threadId": req.threadId} if req.threadId else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        return RunSQLResponseDTO(**data)

    async def ask(
        self, endpoint: str, req: AskRequestDTO, db: Session
    ) -> AsyncIterator[bytes]:
        chatbot = self._get_chatbot(db, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            "returnBothSqlDialect": True,
        }
        if req.threadId:
            payload["threadId"] = req.threadId
        async for chunk in self.post_stream(
            path=endpoint, payload=payload, token=chatbot.wren_key
        ):
            yield chunk

    async def run_chart(
        self, endpoint: str, req: ChartRequestDTO, db: Session
    ) -> ChartResponseDTO:
        chatbot = self._get_chatbot(db, req.org_id)
        payload = {
            "projectId": chatbot.wren_project_id,
            "question": req.question,
            "customInstruction": f"{req.customInstruction} chart",
            "sql": req.sql,
            **({"threadId": req.threadId} if req.threadId else {}),
        }
        data = await self.post(path=endpoint, payload=payload, token=chatbot.wren_key)
        return ChartResponseDTO(**data)

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
