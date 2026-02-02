from enum import Enum
from pydantic import BaseModel


class InsightInfoRequestDTO(BaseModel):
    table_location: str
    type: str


class InsightAnalysisRequestDTO(BaseModel):
    ads_str: str
    start_date: str
    end_date: str


class InsightAdsResponseDTO(BaseModel):
    """Response DTO for insight ads info endpoint."""

    matched_ads_type: list[str]


class InsightStreamType(str, Enum):
    START = "start"
    PROGRESS = "progress"
    RESULT = "result"


class InsightStreamResponseDTO(BaseModel):
    """
    Streaming response DTO for insight analysis.
    Each line in the NDJSON stream follows this format.
    """

    type: InsightStreamType
    message: str
