from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.dtos.business_module_dto import BusinessModuleDTO
from app.dtos.insight_dto import (
    InsightAnalysisRequestDTO,
    InsightAdsResponseDTO,
    InsightStreamResponseDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.services import business_module_service
from app.services.jwt_service import token_required
from app.services import google_sheet_service


router = APIRouter(prefix="/business_module", tags=["Business_module"])
si_router = APIRouter(prefix="/business_module", tags=["Business_module"])

google_sheet_router = APIRouter(prefix="/google_sheet", tags=["Business_module"])


@router.get("/list", response_model=List[BusinessModuleDTO])
@router_try()
def get_business_module(
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
):
    """
    Get current user SI
    """
    return business_module_service.get_business_module(db)


@google_sheet_router.get(
    "/records",
    deprecated=True,
)
@router_try()
def get_google_sheet_records(
    spreadsheet_id: str = Query(..., description="Google Sheet ID from URL"),
    sheet_name: Optional[str] = Query(None, description="Sheet/tab name"),
    user_info: UserReadDTO = Depends(token_required),
) -> List[Dict[str, Any]]:
    """
    Read data from a private Google Sheet as list of dictionaries.
    Uses first row as headers/keys.

    The spreadsheet_id can be found in the Google Sheet URL:
    https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit
    """
    return google_sheet_service.get_sheet_as_dicts(
        spreadsheet_id=spreadsheet_id,
        sheet_name=sheet_name,
    )


@si_router.get(
    "/{si_id}/org/{org_id}/insight-ads",
    response_model=InsightAdsResponseDTO,
)
@router_try()
async def get_insight_ads(
    si_id: int,
    org_id: int,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> InsightAdsResponseDTO:
    """
    Get available ads list for insight analysis.
    """
    return await business_module_service.get_org_insight_info(db, si_id, org_id)


@si_router.post(
    "/{si_id}/org/{org_id}/insight-analysis",
    response_model=InsightStreamResponseDTO,
)
@router_try()
async def post_insight_analysis(
    si_id: int,
    org_id: int,
    body: InsightAnalysisRequestDTO,
    db: Session = Depends(get_db),
    user_info: UserReadDTO = Depends(token_required),
) -> StreamingResponse:
    """
    Post insight analysis request and return streaming NDJSON response.

    Response format (each line is a JSON object):
    - `{"type": "start", "message": "=== Run starting ==="}`
    - `{"type": "progress", "message": "..."}`
    - `{"type": "result", "message": "..."}`
    """
    stream = await business_module_service.post_org_insight_analysis_stream(
        db, si_id, org_id, body
    )
    return StreamingResponse(stream, media_type="text/event-stream")
