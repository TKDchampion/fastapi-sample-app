import logging
from fastapi import APIRouter, HTTPException, Response
from sqlalchemy.orm import Session
from fastapi.params import Depends
from fastapi.responses import StreamingResponse
import httpx
from app.database import get_db
from app.dtos.user_dto import UserReadDTO
from app.dtos.wren_ai_dto import (
    AskRequestDTO,
    AskResponse,
    ChartRequestDTO,
    ChartResponseDTO,
    GenerateSQLRequestDTO,
    GenerateSQLResponseDTO,
    QueryTableMessageResponseDTO,
    QueryTablesRequestDTO,
    RunSQLRequestDTO,
    RunSQLResponseDTO,
)
from app.services.wren_ai_service import WrenAiService
from app.services.jwt_service import token_required


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wren_ai", tags=["Wren AI"])


@router.post("/generatesql", response_model=GenerateSQLResponseDTO)
async def generate_sql_endpoint(
    request_dto: GenerateSQLRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    """
    Asks questions to the LLM and returns the generated SQL query through Wren AI service.
    """
    try:
        return await service.generate_sql("generate_sql", request_dto, db)
    except httpx.HTTPStatusError as exc:
        # For the third-party service error response
        logger.error("HTTPStatusError calling generatesql: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=exc.response.status_code, detail=exc.response.text
        )
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise


@router.post("/runsql", response_model=RunSQLResponseDTO)
async def run_sql_endpoint(
    request_dto: RunSQLRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    """
    Runs a SQL query against the Wren database and returns the results.
    """
    try:
        return await service.run_sql("run_sql", request_dto, db)
    except httpx.HTTPStatusError as exc:
        # For the third-party service error response
        logger.error("RequestError calling run_sql: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=exc.response.status_code, detail=exc.response.text
        )
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise


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
async def ask_endpoint(
    request_dto: AskRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> StreamingResponse:
    """
    Runs a SQL query against the Wren database and returns the results as a stream.
    """
    try:
        # credits = user_info.credits
        # if credits is not None and credits <= 0:
        #     raise HTTPException(
        #         status_code=403,
        #         detail={"msg": "You have no credits left", "type": "no_credits"},
        #     )
        return StreamingResponse(
            service.ask("stream/ask", request_dto, db),
            media_type="text/event-stream",
        )
    except httpx.RequestError as exc:
        logger.error("RequestError calling stream/ask: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=exc.response.status_code,
            detail={"type": "wren_ai", "msg": exc.response.text},
        )
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail={"type": "error", "msg": e.detail.get("msg", "Unknown error")},
        )


@router.post("/chart", response_model=ChartResponseDTO)
async def run_chart_endpoint(
    request_dto: ChartRequestDTO,
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    """
    Runs a SQL query and chart type against the Wren database and returns the chart data.
    """
    try:
        return await service.run_chart("generate_vega_chart", request_dto, db)
    except httpx.HTTPStatusError as exc:
        # For the third-party service error response
        logger.error("RequestError calling run_chart: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=exc.response.status_code,
            detail={"type": "wren_ai", "msg": exc.response.text},
        )
    except Exception as e:
        logger.error("Exception message : %s", e, exc_info=True)
        raise


# @router.post(
#     "/download_table",
#     response_class=Response,
#     responses={
#         200: {
#             "content": {
#                 "application/json": {
#                     "schema": QueryTableMessageResponseDTO.model_json_schema()
#                 },
#                 "text/csv": {"schema": {"type": "string", "format": "binary"}},
#             },
#             "description": "Returns a CSV file if the row count is below limit, otherwise a JSON message.",
#         }
#     },
# )
# async def download_table_endpoint(
#     request_dto: QueryTablesRequestDTO,
#     service: WrenAiService = Depends(WrenAiService),
#     user_info: UserReadDTO = Depends(token_required),
# ):
#     """
#     Downloads table data based on a SQL query from Google BigQuery.
#     """
#     try:
#         return await service.download_table(request_dto.query)

#     except HTTPException as e:
#         raise
#     except Exception as e:
#         logger.error("Error in download_table_endpoint: %s", e, exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal Server Error")
