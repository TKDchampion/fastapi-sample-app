import os
from typing import Any
import httpx
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from dotenv import load_dotenv

from app.domain.exception.domain_exception import DomainException

load_dotenv()

CLOUD_RUN_AUDIENCE = os.getenv("CLOUD_RUN_AUDIENCE", "")
INSIGHT_API_URL = f"{CLOUD_RUN_AUDIENCE}/get_info"
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "1800"))


def _get_id_token(target_audience: str) -> str:
    """
    Generate ID Token using Application Default Credentials (ADC) for Cloud Run authentication.
    """
    return id_token.fetch_id_token(Request(), target_audience)


async def get_insight_info(table_location: str, type: str) -> Any:
    """
    Call Cloud Run insight API with ID Token authentication.
    """
    try:
        # Get ID Token for Cloud Run authentication
        token = _get_id_token(CLOUD_RUN_AUDIENCE)

        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(
                INSIGHT_API_URL,
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
