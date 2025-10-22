import os
import httpx
from typing import AsyncIterator, Optional, Dict, Any


class BaseHTTPService:
    """
    A generic HTTP client base service that supports GET, POST, and other methods.
    The base URL can be set via environment variables.
    Each method also supports an optional `override_base_url` for full flexibility.
    """

    def __init__(self, base_url_env: str, default_base_url: str, timeout: float = 10.0):
        self.base_url: str = os.getenv(base_url_env, default_base_url)
        self.timeout = timeout

    async def post(
        self,
        path: str,
        payload: Dict[str, Any],
        token: Optional[str] = None,
        override_base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        base = override_base_url or self.base_url
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        if token:
            headers["authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def post_stream(
        self,
        path: str,
        payload: Dict[str, Any],
        token: Optional[str] = None,
        override_base_url: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        base = override_base_url or self.base_url
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "accept": "text/event-stream",
            "content-type": "application/json",
        }
        if token:
            headers["authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", url, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_raw():
                    yield chunk

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
        override_base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        base = override_base_url or self.base_url
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        headers = {"accept": "application/json"}
        if token:
            headers["authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
