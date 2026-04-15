import logging
import uuid
from typing import Literal, Optional
from fastapi import APIRouter, File, Query, Response, UploadFile
from sqlalchemy.orm import Session
from fastapi.params import Depends
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.dtos.user_dto import UserReadDTO
from app.dtos.wren_ai_dto import (
    ArtifactReadDTO,
    AskRequestDTO,
    AskResponse,
    CsvUploadResponseDTO,
    ChatbotReadDTO,
    ChartRequestDTO,
    ChartResponseDTO,
    GenerateSQLRequestDTO,
    GenerateSQLResponseDTO,
    QueryTableMessageResponseDTO,
    QueryTablesRequestDTO,
    RenameThreadRequestDTO,
    RunSQLRequestDTO,
    RunSQLResponseDTO,
    MessageListResponseDTO,
    ThreadListResponseDTO,
    ThreadReadDTO,
)
from app.decorators.router_try import router_try
from app.services.wren_ai_service import WrenAiService
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wren_ai", tags=["Wren AI"])


@router.get(
    "/si/{si_id}/org/{org_id}/chat/threads", response_model=ThreadListResponseDTO
)
@router_try()
def get_threads_endpoint(
    si_id: int,
    org_id: int,
    chatbot_id: Optional[int] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return service.get_threads(
        db, user_info, si_id, org_id, user_info.id, chatbot_id, cursor, limit
    )


@router.patch(
    "/si/{si_id}/org/{org_id}/chat/threads/{thread_id}",
    response_model=ThreadReadDTO,
)
@router_try()
def rename_thread_endpoint(
    si_id: int,
    org_id: int,
    thread_id: str,
    body: RenameThreadRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return service.rename_thread(
        db, user_info, si_id, org_id, uuid.UUID(thread_id), body.title
    )


@router.delete(
    "/si/{si_id}/org/{org_id}/chat/threads/{thread_id}",
    status_code=204,
)
@router_try()
def delete_thread_endpoint(
    si_id: int,
    org_id: int,
    thread_id: str,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    service.delete_thread(db, user_info, si_id, org_id, uuid.UUID(thread_id))


@router.get(
    "/si/{si_id}/org/{org_id}/chat/threads/{thread_id}/messages",
    response_model=MessageListResponseDTO,
)
@router_try()
def get_messages_endpoint(
    si_id: int,
    org_id: int,
    thread_id: str,
    cursor: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    order: Literal["asc", "desc"] = Query("asc"),
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return service.get_messages(
        db,
        user_info,
        si_id,
        org_id,
        uuid.UUID(thread_id),
        cursor,
        limit,
        order,
    )


@router.get(
    "/si/{si_id}/org/{org_id}/chat/thread/{thread_id}/message/{message_id}/artifact/{artifact_id}",
    response_model=ArtifactReadDTO,
)
@router_try()
def get_artifact_endpoint(
    si_id: int,
    org_id: int,
    thread_id: str,
    message_id: str,
    artifact_id: str,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return service.get_artifact(
        db,
        user_info,
        si_id,
        org_id,
        uuid.UUID(thread_id),
        uuid.UUID(message_id),
        uuid.UUID(artifact_id),
    )


@router.get("/si/{si_id}/org/{org_id}/chatbot", response_model=ChatbotReadDTO)
@router_try()
def get_chatbot_endpoint(
    si_id: int,
    org_id: int,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return service.get_chatbot(db, user_info, si_id, org_id)


@router.post("/generatesql", response_model=GenerateSQLResponseDTO)
@router_try()
async def generate_sql_endpoint(
    request_dto: GenerateSQLRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return await service.generate_sql("generate_sql", request_dto, db, user_info)


@router.post("/runsql", response_model=RunSQLResponseDTO)
@router_try()
async def run_sql_endpoint(
    request_dto: RunSQLRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return await service.run_sql("run_sql", request_dto, db, user_info)


@router.post(
    "/ask",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Server-Sent Events stream of SQL and summary stages",
            "content": {"text/event-stream": {"examples": AskResponse}},
        }
    },
)
@router_try()
async def ask_endpoint(
    request_dto: AskRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> StreamingResponse:
    stream = await service.ask("stream/ask", request_dto, db, user_info)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chart", response_model=ChartResponseDTO)
@router_try()
async def run_chart_endpoint(
    request_dto: ChartRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return await service.run_chart("generate_vega_chart", request_dto, db, user_info)


@router.post(
    "/si/{si_id}/org/{org_id}/csv",
    response_model=CsvUploadResponseDTO,
    status_code=201,
)
@router_try()
def upload_csv_endpoint(
    si_id: int,
    org_id: int,
    file: UploadFile = File(...),
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return service.upload_csv(db, user_info, si_id, org_id, file)


@router.post(
    "/download_table",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/json": {
                    "schema": QueryTableMessageResponseDTO.model_json_schema()
                },
                "text/csv": {"schema": {"type": "string", "format": "binary"}},
            },
            "description": "Returns a CSV file if the row count is below limit, otherwise a JSON message.",
        }
    },
)
@router_try()
async def download_table_endpoint(
    request_dto: QueryTablesRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
):
    return await service.download_table(request_dto.query)
