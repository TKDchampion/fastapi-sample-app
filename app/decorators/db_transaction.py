from functools import wraps
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.exception.domain_exception import DomainException


def db_tx(func):
    @wraps(func)
    def wrapper(db: Session, *args, **kwargs):
        try:
            result = func(db, *args, **kwargs)
            db.commit()
            return result

        except DomainException as e:
            db.rollback()
            raise HTTPException(
                status_code=e.code,
                detail={"msg": e.msg, "type": e.type},
            )

        except HTTPException:
            db.rollback()
            raise

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={"msg": "Unknown error", "type": "internal_error"},
            )

    return wrapper
