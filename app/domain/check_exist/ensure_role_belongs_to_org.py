from fastapi import HTTPException
from app.repositories import role_repository


def ensure_role_belongs_to_org(db, role_id, org_id):
    role = role_repository.role_belongs_to_org(db, role_id, org_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail={"msg": "Role not found in this org", "type": "role_not_found"},
        )
    return role
