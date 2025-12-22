from fastapi import HTTPException
from app.repositories import user_repository


def ensure_user_exists(db, user_id):
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"msg": "User not found", "type": "user_not_found"},
        )
    return user
