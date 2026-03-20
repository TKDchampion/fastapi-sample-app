import logging
from fastapi import APIRouter, Response
from sqlalchemy.orm import Session
from fastapi.params import Depends
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.dtos.user_dto import UserReadDTO
from app.dtos.wren_ai_dto import (
    AskRequestDTO,
    AskResponse,
    ChatbotReadDTO,
    ChartRequestDTO,
    ChartResponseDTO,
    GenerateSQLRequestDTO,
    GenerateSQLResponseDTO,
    QueryTableMessageResponseDTO,
    QueryTablesRequestDTO,
    RunSQLRequestDTO,
    RunSQLResponseDTO,
)
from app.decorators.router_try import router_try
from app.services.wren_ai_service import WrenAiService
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wren_ai", tags=["Wren AI"])


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
