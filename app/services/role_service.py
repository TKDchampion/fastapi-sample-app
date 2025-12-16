from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import OrgWriteParamsDTO
from app.domain.check_exist import (
    ensure_org_write_permission,
    ensure_role_belongs_to_org,
    ensure_user_exists,
    ensure_user_role_exists,
)
from app.domain.exception.domain_exception import DomainException
from app.dtos.role_dto import (
    AssignRoleParamDTO,
    RolePermissionDTO,
    UpdateUserRoleResponseDTO,
)
from app.dtos.user_dto import UserReadDTO
from app.repositories import role_repository
from app.services import user_service
from app.services.permission_guard_service import verify_org_write_permission


@db_tx
def assign_role_to_user(db: Session, param: AssignRoleParamDTO, user_info: UserReadDTO):

    ensure_org_write_permission(db, user_info, param.si_id, param.org_id)

    user = user_service.get_user_by_email(db, param.email)
    if not user:
        raise DomainException("User not found", "user_not_found", 404)

    ensure_role_belongs_to_org(db, param.role_id, param.org_id)

    # Create role
    new_user_role = role_repository.create_user_role(
        db, param.org_id, param.role_id, user.id
    )

    return {
        "msg": "Role assigned",
        "user_id": user.id,
        "role_id": param.role_id,
        "org_id": param.org_id,
        "data": new_user_role._mapping,
    }


def roles_by_org(db: Session, org_id: int):
    try:
        return role_repository.roles_by_org(db, org_id)
    except HTTPException:
        raise


@db_tx
def update_user_role(
    db: Session,
    si_id: int,
    org_id: int,
    user_id: int,
    role_id: int,
    user_info: UserReadDTO,
):

    ensure_org_write_permission(db, user_info, si_id, org_id)
    ensure_user_exists(db, user_id)
    ensure_role_belongs_to_org(db, role_id, org_id)
    ensure_user_role_exists(db, user_id, org_id)

    role_repository.update_user_role(
        db=db,
        user_id=user_id,
        org_id=org_id,
        role_id=role_id,
    )

    # Get updated role with permissions
    role = role_repository.get_role_with_permissions(db, role_id)

    return UpdateUserRoleResponseDTO(
        role_name=role.name,
        permissions=[perm.key for perm in role.permissions],
    )


@db_tx
def delete_user_role(
    db: Session,
    si_id: int,
    org_id: int,
    user_id: int,
    user_info: UserReadDTO,
):

    ensure_org_write_permission(db, user_info, si_id, org_id)
    ensure_user_exists(db, user_id)
    ensure_user_role_exists(db, user_id, org_id)

    deleted = role_repository.delete_user_role(
        db=db,
        user_id=user_id,
        org_id=org_id,
    )

    return {
        "msg": "Role deleted",
        "user_id": user_id,
        "org_id": org_id,
        "deleted": deleted,
    }
