from fastapi import HTTPException
from app.repositories import role_repository


def ensure_user_role_exists(db, user_id, org_id):
    user_role = role_repository.get_user_role(db, user_id, org_id)
    if not user_role:
        raise HTTPException(
            status_code=404,
            detail={
                "msg": "User has no role in this org",
                "type": "user_role_not_found",
            },
        )
    return user_role
