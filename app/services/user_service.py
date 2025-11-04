from collections import defaultdict
from typing import Dict, List, Set, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.entities.organization_entity import OrganizationEntity
from app.repositories import user_repository
from app.dtos.user_dto import (
    OrgNodeDTO,
    PermissionTreeDTO,
    SINodeDTO,
    UserAccessTreeResponseDTO,
    UserCreateDTO,
    UserReadDTO,
)


def get_users(db: Session):
    return user_repository.get_all_users(db)


def add_user(db: Session, user: UserCreateDTO):
    return user_repository.create_user(db, user)


def get_user_by_email(db: Session, email: str):
    return user_repository.get_user_by_email(db, email)


def build_for_user(db: Session, user_id: int) -> UserAccessTreeResponseDTO:
    user = user_repository.fetch_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role_rows = user_repository.fetch_user_roles_joined(db, user_id)

    # ---- quick exits / collections ----
    has_super = any(r.scope_type == "super" for r in role_rows)
    all_permission_names = user_repository.fetch_all_permissions(db)

    if has_super:
        # SUPER: full access to every SI & Org with all permissions
        all_si, all_org = user_repository.fetch_all_sis_and_orgs(db)

        # map SI -> its orgs (one pass, no extra SQL)
        orgs_by_si: Dict[int, List[OrganizationEntity]] = defaultdict(list)
        for o in all_org:
            orgs_by_si[o.si_id].append(o)

        si_nodes: List[SINodeDTO] = []
        for si in all_si:
            org_nodes = [
                OrgNodeDTO(
                    id=o.id,
                    name=o.name,
                    role="owner",
                    isActive=True,
                    permissions=all_permission_names,
                )
                for o in orgs_by_si.get(si.id, [])
            ]
            si_nodes.append(
                SINodeDTO(
                    id=si.id,
                    name=si.name,
                    isActive=True,
                    accessibleNode=org_nodes,
                )
            )

        tree = PermissionTreeDTO(isActive=True, accessibleNode=si_nodes)
        return UserAccessTreeResponseDTO(
            user=UserReadDTO.from_entity(user), permissionTree=tree
        )

    # ---- aggregate by scope/role ----
    # three purposes:
    # 1) collect SI ids with admin role (scope=si)
    # 2) collect ORG roles (scope=org)
    # 3) map each (scope_type, scope_id, role_id) -> permissions
    si_ids_with_admin: Set[int] = set()
    org_scope_ids: Set[int] = set()
    si_scope_ids: Set[int] = set()

    # permissions grouped by (scope_type, scope_id, role_id)
    perms_group: Dict[Tuple[str, int, int], Set[str]] = defaultdict(set)
    role_names: Dict[int, str] = {}

    for r in role_rows:
        role_names[r.role_id] = r.role_name
        if r.permission_name:
            perms_group[(r.scope_type, r.scope_id, r.role_id)].add(r.permission_name)

        if r.scope_type == "si":
            si_scope_ids.add(r.scope_id)
            # Treat having any SI role as "admin at SI level" if that’s your rule.
            # If only certain roles are admins, you can filter here by r.role_name or a flag on RoleEntity.
            si_ids_with_admin.add(r.scope_id)
        elif r.scope_type == "org":
            org_scope_ids.add(r.scope_id)

    # bulk-load entities for names
    si_map = user_repository.fetch_sis_by_ids(db, si_scope_ids | si_ids_with_admin)
    org_map = user_repository.fetch_orgs_by_ids(db, org_scope_ids)

    # also need all orgs under si admin
    orgs_by_si_admin = user_repository.fetch_orgs_under_si_ids(db, si_ids_with_admin)

    # prepare SI node shell (we’ll append org children next)
    si_nodes_map: Dict[int, SINodeDTO] = {}
    for si_id in si_scope_ids | si_ids_with_admin:
        si = si_map.get(si_id)
        if not si:
            # dangling role → skip
            continue
        # isActive=True when user has any role at SI scope; otherwise False (will become True anyway if in si_ids_with_admin)
        si_nodes_map[si_id] = SINodeDTO(
            id=si.id,
            name=si.name,
            isActive=(si_id in si_ids_with_admin) or (si_id in si_scope_ids),
            accessibleNode=[],
        )

    # 1) Org roles explicitly assigned (scope=org)
    for (scope_type, scope_id, role_id), perm_set in perms_group.items():
        if scope_type != "org":
            continue
        org = org_map.get(scope_id)
        if not org:
            continue
        si = si_map.get(org.si_id)
        if not si:
            continue

        # ensure SI node exists (may not if user only has org role under SI they don’t otherwise hold)
        if si.id not in si_nodes_map:
            si_nodes_map[si.id] = SINodeDTO(
                id=si.id,
                name=si.name,
                isActive=False,
                accessibleNode=[],
            )

        # override permission to "all" if SI admin exists
        if si.id in si_ids_with_admin:
            permissions = all_permission_names
            role_name = "owner"
            is_active = True
        else:
            permissions = sorted(perm_set)
            role_name = role_names.get(role_id, "member")
            is_active = any(
                rr.scope_type == "org"
                and rr.scope_id == scope_id
                and (rr.isActiveOrg or False)
                for rr in role_rows
            )

        si_nodes_map[si.id].accessibleNode.append(
            OrgNodeDTO(
                id=org.id,
                name=org.name,
                role=role_name,
                isActive=is_active,
                permissions=permissions,
            )
        )

    # 2) Add all orgs under SI-admin that weren’t added yet
    for si_id in si_ids_with_admin:
        si_node = si_nodes_map.get(si_id)
        if not si_node:
            si = si_map.get(si_id)
            if not si:
                continue
            si_node = SINodeDTO(
                id=si.id, name=si.name, isActive=True, accessibleNode=[]
            )
            si_nodes_map[si_id] = si_node

        existing_org_ids = {n.id for n in si_node.accessibleNode}
        for org in orgs_by_si_admin.get(si_id, []):
            if org.id in existing_org_ids:
                continue
            si_node.accessibleNode.append(
                OrgNodeDTO(
                    id=org.id,
                    name=org.name,
                    role="owner",
                    isActive=True,
                    permissions=all_permission_names,
                )
            )

    # finalize
    si_nodes = list(si_nodes_map.values())
    # (Optional) stable sort for determinism
    si_nodes.sort(key=lambda x: (x.name or "", x.id))
    for node in si_nodes:
        node.accessibleNode.sort(key=lambda x: (x.name or "", x.id))

    tree = PermissionTreeDTO(isActive=bool(si_nodes), accessibleNode=si_nodes)
    return UserAccessTreeResponseDTO(
        user=UserReadDTO.model_validate(user), permissionTree=tree
    )
