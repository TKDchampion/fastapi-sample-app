from functools import wraps
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.domain.exception.domain_exception import DomainException

logger = logging.getLogger(__name__)


def db_tx(func):
    @wraps(func)
    def wrapper(db: Session, *args, **kwargs):
        try:
            result = func(db, *args, **kwargs)
            db.commit()
            return result

        except HTTPException:
            db.rollback()
            raise

        except DomainException as e:
            db.rollback()
            logger.error("DomainException: %s", e, exc_info=True)
            raise HTTPException(
                status_code=e.code,
                detail={"msg": e.msg, "type": e.type},
            )

        except IntegrityError as e:
            db.rollback()
            logger.error("IntegrityError: %s", e, exc_info=True)
            raise HTTPException(
                status_code=400,
                detail={"type": "db_integrity_error", "msg": str(e.orig)},
            )

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("SQLAlchemyError: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"type": "db_sqlalchemy_error", "msg": "Database error"},
            )

        except Exception as e:
            db.rollback()
            logger.error("Exception: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"msg": "Unknown error", "type": "internal_error"},
            )

    return wrapper
