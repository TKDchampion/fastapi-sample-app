import asyncio
import logging
from functools import wraps
from fastapi import HTTPException

from app.domain.exception.domain_exception import DomainException

logger = logging.getLogger(__name__)


def router_try():
    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)

                except HTTPException:
                    raise

                except DomainException as e:
                    raise HTTPException(
                        status_code=e.code,
                        detail={"type": e.type, "msg": e.msg},
                    )

                except Exception as e:
                    logger.error("Unhandled exception in %s: %s", func.__name__, e, exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail={"type": "error", "msg": "Unknown error"},
                    )

            return async_wrapper
        else:

            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)

                except HTTPException:
                    raise

                except DomainException as e:
                    raise HTTPException(
                        status_code=e.code,
                        detail={"type": e.type, "msg": e.msg},
                    )

                except Exception as e:
                    logger.error("Unhandled exception in %s: %s", func.__name__, e, exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail={"type": "error", "msg": "Unknown error"},
                    )

            return wrapper

    return decorator
