from sqlalchemy.orm import Session
from app.repositories import user_repository
from app.dtos.user_dto import (
    UserSIListItemDTO,
    UserSIListResponseDTO,
)


def get_user_si(db: Session, user_id: int):
    roles = user_repository.get_user_roles(db, user_id)
    has_super = any(r.scope_type == "super" for r in roles)

    if has_super:
        sis = user_repository.get_si_all(db)
    else:
        sis = user_repository.get_si_user_roles(db, user_id)

    items = [UserSIListItemDTO.model_validate(row) for row in sis]

    return UserSIListResponseDTO(si=items)
