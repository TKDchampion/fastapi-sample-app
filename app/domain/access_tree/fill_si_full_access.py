from app.repositories import user_repository


def fill_si_full_access(si_map: dict, perms_by_type, db):
    full_si_ids = [
        sid for sid, v in si_map.items() if v["permissions"] == perms_by_type["si"]
    ]

    if not full_si_ids:
        return

    orgs_all = user_repository.get_all_orgs(db)

    for oid, oname, sid_fk in orgs_all:
        if sid_fk in full_si_ids:
            exists = {o["id"] for o in si_map[sid_fk]["accessibleNode"]}
            if oid not in exists:
                si_map[sid_fk]["accessibleNode"].append(
                    {
                        "level": "org",
                        "id": oid,
                        "name": oname,
                        "role": "owner",
                        "isActive": True,
                        "permissions": perms_by_type["org"],
                    }
                )
