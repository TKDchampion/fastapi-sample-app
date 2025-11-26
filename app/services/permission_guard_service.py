# app/services/permission_guard_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import OrgWriteParamsDTO, can_write_org
from app.domain.exception.domain_exception import DomainException
from app.dtos.user_dto import UserReadDTO
from app.repositories import org_repository
from app.services.user_service import get_user_access_tree


@db_tx
def verify_org_write_permission(
    db: Session,
    user: UserReadDTO,
    params: OrgWriteParamsDTO,
):
    """
    驗證使用者是否有權限。
    """
    if params.si_id and params.org_id:
        print(params)
        org_detail = org_repository.get_org_by_sid_oid(db, params.si_id, params.org_id)
        if org_detail is None:
            raise HTTPException(
                status_code=404,
                detail={"type": "not_found", "msg": "Not found"},
            )

    access_tree = get_user_access_tree(db, user)

    if not can_write_org(access_tree, params):
        raise DomainException("Insufficient permission", "no_access", 403)

    return {"isAccess": True, "org_detail": org_detail or None}
