from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories import user_repository
from app.dtos.user_dto import (
    UserOrgListItemDTO,
    UserOrgListResponseDTO,
)


def get_organizations_by_si_id(db: Session, si_id: int):
    orgs = user_repository.get_organizations_by_si_id(db, si_id)

    if not orgs:
        raise HTTPException(
            status_code=404,
            detail={"type": "error", "msg": "Error ID"},
        )

    items = [
        UserOrgListItemDTO.model_validate(org, from_attributes=True) for org in orgs
    ]

    return UserOrgListResponseDTO(org=items)
