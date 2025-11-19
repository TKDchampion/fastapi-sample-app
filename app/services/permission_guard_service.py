# app/services/permission_guard_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.domain.access_tree.check_user_access import OrgWriteParams, can_write_org
from app.dtos.user_dto import UserReadDTO
from app.services.user_service import get_user_access_tree


def verify_org_write_permission(
    db: Session,
    user: UserReadDTO,
    params: OrgWriteParams,
):
    """
    驗證使用者是否有權限。
    """

    access_tree = get_user_access_tree(db, user)

    if not can_write_org(access_tree, params):
        raise HTTPException(status_code=403, detail="Insufficient permission")

    return True
