def build_si_map(roles, perms_by_type):
    si_map: dict[int, dict] = {}

    for r in roles:
        # SI level role
        if r.scope_type == "si":
            si_map[r.si_id] = {
                "level": "si",
                "id": r.si_id,
                "name": r.si_name,
                "isActive": bool(r.isActive),
                "role": r.role_name,
                "permissions": perms_by_type["si"],  # full si perms by role
                "accessibleNode": [],
            }

        # ORG role
        elif r.scope_type == "org":
            if r.si_id not in si_map:
                si_map[r.si_id] = {
                    "level": "si",
                    "id": r.si_id,
                    "name": r.si_name,
                    "isActive": False,
                    "role": None,
                    "permissions": [],
                    "accessibleNode": [],
                }

            si_map[r.si_id]["accessibleNode"].append(
                {
                    "level": "org",
                    "id": r.org_id,
                    "name": r.org_name,
                    "role": r.role_name,
                    "isActive": bool(r.isActive),
                    "permissions": [r.perm_name],
                }
            )

    return si_map
