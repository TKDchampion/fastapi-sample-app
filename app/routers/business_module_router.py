from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.decorators import router_try
from app.dtos.business_module_dto import BusinessModuleDTO
from app.dtos.user_dto import UserReadDTO
from app.services import business_module_service
from app.services.jwt_service import token_required
from app.services import google_sheet_service
from app.services import insight_service


router = APIRouter(prefix="/business_module", tags=["Business_module"])
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


@router.get("/insight-info")
@router_try()
async def get_insight_info(
    table_location: str = Query(..., description="BigQuery table location"),
    type: str = Query(..., description="Save type"),
) -> Any:
    """
    Call Cloud Run insight API to get info (GET with query parameters).
    """
    return await insight_service.get_insight_info(
        table_location=table_location,
        type=type,
    )
