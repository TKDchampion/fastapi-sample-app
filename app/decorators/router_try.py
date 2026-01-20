import asyncio
from functools import wraps
from fastapi import HTTPException


def router_try():
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)

                except HTTPException:
                    raise

                except Exception as e:
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

                except Exception as e:
                    # 統一輸出 500
                    raise HTTPException(
                        status_code=500,
                        detail={"type": "error", "msg": "Unknown error"},
                    )

            return wrapper

    return decorator
