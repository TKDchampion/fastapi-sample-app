from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.domain.access_tree.check_user_access import OrgWriteParamsDTO
from app.dtos.permission_dto import RolePermissionDTO
from app.dtos.user_dto import UserReadDTO
from app.repositories import permission_repository
from app.services.permission_guard_service import verify_org_write_permission


@db_tx
def get_role_permissions(
    db: Session,
    si_id: int,
    org_id: int,
    user_info: UserReadDTO,
):
    params = OrgWriteParamsDTO(si_id=si_id, org_id=org_id, perm="org.permission.view")
    verify_org_write_permission(db, user_info, params)
    roles = permission_repository.get_roles_with_permissions(db, org_id)

    response = []
    for role in roles:
        response.append(
            RolePermissionDTO(
                id=role.id,
                name=role.name,
                permissions=[perm.id for perm in role.permissions],
            )
        )

    return response
