import inspect
import logging
from functools import wraps
from typing import Optional

import httpx

from app.domain.exception.domain_exception import DomainException

logger = logging.getLogger(__name__)


def external_api(error_type: str, default_msg: Optional[str] = None):
    """
    Dual-use decorator: works on async functions OR classes that extend BaseHTTPService.

    Function usage:
        @external_api("insight_ai")
        async def call_insight_api(): ...

    Class usage:
        @external_api("wren_ai")
        class WrenAiService(BaseHTTPService): ...

        Injects into the class:
        - service_name       → error_type string
        - _call(method, ...) → wraps super() HTTP call with unified error handling
        - post(**kwargs)     → delegates to _call("post", ...)
        - get(**kwargs)      → delegates to _call("get", ...)
    """
    msg_prefix = default_msg or "External API"

    def _handle_exc(e: Exception) -> None:
        if isinstance(e, httpx.HTTPStatusError):
            logger.error(
                "%s HTTPStatusError [%s]: %s",
                error_type, e.response.status_code, e.response.text,
                exc_info=True,
            )
            raise DomainException(msg=e.response.text, type=error_type, code=e.response.status_code)
        if isinstance(e, httpx.RequestError):
            logger.error("%s RequestError: %s", error_type, e, exc_info=True)
            raise DomainException(msg=f"{msg_prefix} request failed: {e}", type=error_type, code=500)
        logger.error("%s unexpected error: %s", error_type, e, exc_info=True)
        raise DomainException(msg=f"{msg_prefix} unexpected error: {e}", type=error_type, code=500)

    def _decorate_class(cls):
        cls.service_name = error_type

        async def _call(self, method: str, **kwargs):
            try:
                return await getattr(super(cls, self), method)(**kwargs)
            except DomainException:
                raise
            except Exception as e:
                _handle_exc(e)

        async def post(self, **kwargs):
            return await self._call("post", **kwargs)

        async def get(self, **kwargs):
            return await self._call("get", **kwargs)

        cls._call, cls.post, cls.get = _call, post, get
        return cls

    def _decorate_func(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except DomainException:
                    raise
                except Exception as e:
                    _handle_exc(e)
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except DomainException:
                    raise
                except Exception as e:
                    _handle_exc(e)
        return wrapper

    def decorator(target):
        return _decorate_class(target) if isinstance(target, type) else _decorate_func(target)

    return decorator
