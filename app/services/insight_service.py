import json
import os
from typing import Any, AsyncIterator
import httpx
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from dotenv import load_dotenv

from app.decorators import external_api
from app.domain.exception.domain_exception import DomainException
from app.dtos.insight_dto import InsightStreamResponseDTO, InsightStreamType

load_dotenv()

CLOUD_RUN_AUDIENCE = os.getenv("CLOUD_RUN_AUDIENCE", "")
INSIGHT_GET_INFO_API_URL = f"{CLOUD_RUN_AUDIENCE}/get_info"
INSIGHT_POST_ANALYSIS_API_URL = f"{CLOUD_RUN_AUDIENCE}/report"
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "1800"))
STREAM_TIMEOUT_SECONDS = float(os.getenv("STREAM_TIMEOUT_SECONDS", "1800"))


def _get_id_token(target_audience: str) -> str:
    """
    Generate ID Token using Application Default Credentials (ADC) for Cloud Run authentication.
    """
    return id_token.fetch_id_token(Request(), target_audience)


@external_api("insight_ai", "Insight API")
async def get_insight_info(table_location: str, type: str) -> Any:
    """
    Call Cloud Run insight API with ID Token authentication.
    """
    token = _get_id_token(CLOUD_RUN_AUDIENCE)

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(
            INSIGHT_GET_INFO_API_URL,
            params={
                "table_location": table_location,
                "type": type,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        return response.json()


async def post_analysis_stream(
    table_location: str,
    type: str,
    ads_str: str,
    start_date: str,
    end_date: str,
) -> AsyncIterator[InsightStreamResponseDTO]:
    """
    Call Cloud Run insight analysis API with streaming response.
    Yields InsightStreamResponseDTO objects parsed from NDJSON stream.

    Note: Cannot use @external_api decorator because this is an async generator.
    """
    try:
        token = _get_id_token(CLOUD_RUN_AUDIENCE)
        timeout = httpx.Timeout(STREAM_TIMEOUT_SECONDS, connect=30.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                INSIGHT_POST_ANALYSIS_API_URL,
                json={
                    "table_location": table_location,
                    "type": type,
                    "ads_str": ads_str,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            ) as response:
                response.raise_for_status()
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            yield InsightStreamResponseDTO(
                                type=InsightStreamType(data["type"]),
                                message=data["message"],
                            )
    except httpx.HTTPStatusError as e:
        raise DomainException(
            msg=f"Insight API error: {e.response.status_code}",
            type="insight_ai",
            code=e.response.status_code,
        )
    except httpx.RequestError as e:
        raise DomainException(
            msg=f"Insight API request failed: {str(e)}",
            type="insight_ai",
            code=500,
        )
    except Exception as e:
        raise DomainException(
            msg=f"Insight API unexpected error: {str(e)}",
            type="insight_ai",
            code=500,
        )
