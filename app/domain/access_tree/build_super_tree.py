from collections import defaultdict
from app.dtos.user_dto import UserReadDTO
from app.repositories import si_repository


def build_super_tree(user, perms_by_type, result, db):
    rows = si_repository.get_si_org_tree(db)

    si_map = defaultdict(lambda: {"name": "", "orgs": []})

    for si_id, si_name, si_logo, org_id, org_name, org_logo in rows:
        si_map[si_id]["name"] = si_name
        si_map[si_id]["logo"] = si_logo

        if org_id:
            si_map[si_id]["orgs"].append((org_id, org_name, org_logo))

    for sid, data in si_map.items():
        result["accessibleNode"].append(
            {
                "level": "si",
                "id": sid,
                "name": data["name"],
                "isActive": True,
                "logo": data["logo"],
                "permissions": perms_by_type["si"],
                "accessibleNode": [
                    {
                        "level": "org",
                        "id": oid,
                        "name": oname,
                        "role": "owner",
                        "isActive": True,
                        "logo": ologo,
                        "permissions": perms_by_type["org"],
                    }
                    for oid, oname, ologo in data["orgs"]
                ],
            }
        )

    return {
        "user": UserReadDTO.model_validate(user),
        "permissionTree": result,
    }
