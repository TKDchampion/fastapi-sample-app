import asyncio
from functools import wraps
from typing import Optional

import httpx

from app.domain.exception.domain_exception import DomainException


def external_api(error_type: str, default_msg: Optional[str] = None):
    """
    Decorator for handling external API errors (httpx calls).

    Catches httpx.HTTPStatusError, httpx.RequestError, and general Exception,
    then converts them to DomainException with the specified error_type.

    Args:
        error_type: The error type to use in DomainException (e.g., "insight_ai", "google_auth")
        default_msg: Optional default message prefix (defaults to "External API")

    Usage:
        @external_api("insight_ai")
        async def call_insight_api():
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
    """
    msg_prefix = default_msg or "External API"

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except DomainException:
                    raise
                except httpx.HTTPStatusError as e:
                    raise DomainException(
                        msg=f"{msg_prefix} error: {e.response.status_code}",
                        type=error_type,
                        code=e.response.status_code,
                    )
                except httpx.RequestError as e:
                    raise DomainException(
                        msg=f"{msg_prefix} request failed: {str(e)}",
                        type=error_type,
                        code=500,
                    )
                except Exception as e:
                    raise DomainException(
                        msg=f"{msg_prefix} unexpected error: {str(e)}",
                        type=error_type,
                        code=500,
                    )

            return async_wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except DomainException:
                    raise
                except httpx.HTTPStatusError as e:
                    raise DomainException(
                        msg=f"{msg_prefix} error: {e.response.status_code}",
                        type=error_type,
                        code=e.response.status_code,
                    )
                except httpx.RequestError as e:
                    raise DomainException(
                        msg=f"{msg_prefix} request failed: {str(e)}",
                        type=error_type,
                        code=500,
                    )
                except Exception as e:
                    raise DomainException(
                        msg=f"{msg_prefix} unexpected error: {str(e)}",
                        type=error_type,
                        code=500,
                    )

            return wrapper

    return decorator
