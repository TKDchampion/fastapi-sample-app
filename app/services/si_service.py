from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.repositories import si_repository, user_repository
from app.dtos.si_dto import (
    SIListItemDTO,
    SIListResponseDTO,
)


@db_tx
def get_user_si(db: Session, user_id: int):
    roles = user_repository.get_user_roles(db, user_id)
    has_super = any(r.scope_type == "super" for r in roles)

    if has_super:
        sis = si_repository.get_si_all(db)
    else:
        sis = user_repository.get_si_user_roles(db, user_id)

    if not sis:
        return SIListResponseDTO(si=[])

    items = [SIListItemDTO(**row) for row in sis]

    return SIListResponseDTO(si=items)
