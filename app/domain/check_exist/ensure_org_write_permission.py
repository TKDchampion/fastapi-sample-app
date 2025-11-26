from app.domain.access_tree.check_user_access import OrgWriteParamsDTO
from app.services.permission_guard_service import verify_org_write_permission


def ensure_org_write_permission(db, user_info, si_id, org_id):
    params = OrgWriteParamsDTO(si_id=si_id, org_id=org_id, perm="member.edit")
    verify_org_write_permission(db, user_info, params)
