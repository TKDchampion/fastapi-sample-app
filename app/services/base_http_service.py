import asyncio
import logging
import os
import httpx
from typing import AsyncIterator, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class BaseHTTPService:
    """
    Generic async HTTP service supporting GET, POST, and streaming POST requests.
    Now supports non-JSON payloads via overridable `prepare_request`.
    """

    def __init__(self, base_url_env: str, default_base_url: str, timeout: float = 60.0):
        self._base_url_env = base_url_env
        self._default_base_url = default_base_url
        self.timeout = timeout

    # ------------------------
    # 🔧 HOOKS (可覆寫)
    # ------------------------
    def get_base_url(self, override_base_url: Optional[str] = None) -> str:
        return override_base_url or os.getenv(
            self._base_url_env, self._default_base_url
        )

    def build_headers(
        self,
        token: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        accept: str = "application/json",
        content_type: Optional[str] = "application/json",
    ) -> Dict[str, str]:
        headers = {"accept": accept}
        if content_type:
            headers["content-type"] = content_type
        if token:
            headers["authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def prepare_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return payload

    def prepare_request(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Default: JSON request.
        Override this if your API uses form-data, raw bytes, or other encodings.

        Returns:
            (request_kwargs, headers)
        Example return for JSON:
            ({"json": payload}, headers)
        """
        return {"json": payload}, headers

    # ------------------------
    # 🌐 HTTP METHODS
    # ------------------------
    async def post(
        self,
        path: str,
        payload: Dict[str, Any],
        token: Optional[str] = None,
        override_base_url: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        base = self.get_base_url(override_base_url)
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        headers = self.build_headers(token, extra_headers)
        payload = self.prepare_payload(payload)

        request_kwargs, headers = self.prepare_request(payload, headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, **request_kwargs)
            response.raise_for_status()
            return response.json()

    async def post_stream(
        self,
        path: str,
        payload: Dict[str, Any],
        token: Optional[str] = None,
        override_base_url: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        base = self.get_base_url(override_base_url)
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"

        # url = f"{self.base_url}/{path}"
        headers = {
            "accept": "text/event-stream",
            "content-type": "application/json",
        }
        if token:
            headers["authorization"] = f"Bearer {token}"

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST", url, json=payload, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_raw():
                        yield chunk
        except httpx.RemoteProtocolError:
            # ✅ 第三方 SSE 先斷
            logger.warning("UPSTREAM_SSE_DISCONNECTED")
            return

        except asyncio.CancelledError:
            # ✅ 前端先斷（refresh / close tab）
            logger.info("CLIENT_DISCONNECTED")
            raise

        except Exception:
            # ✅ backend 自己炸
            logger.exception("BACKEND_EXCEPTION")
            raise

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
        override_base_url: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        base = self.get_base_url(override_base_url)
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        headers = self.build_headers(token, extra_headers, content_type=None)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    async def delete(
        self,
        path: str,
        payload: Dict[str, Any],
        token: Optional[str] = None,
        override_base_url: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        base = self.get_base_url(override_base_url)
        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        headers = self.build_headers(token, extra_headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                "DELETE", url, json=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()
