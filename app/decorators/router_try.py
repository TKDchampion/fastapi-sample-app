from functools import wraps
from fastapi import HTTPException


def router_try():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except HTTPException:
                # 讓 HTTPException 正常拋出，FastAPI 自己會處理
                raise

            except Exception as e:
                # Global logging
                import logging

                logger = logging.getLogger(__name__)
                logger.error("Unhandled exception: %s", e, exc_info=True)

                # 統一輸出 500
                raise HTTPException(
                    status_code=500,
                    detail={"type": "error", "msg": "Unknown error"},
                )

        return wrapper

    return decorator
