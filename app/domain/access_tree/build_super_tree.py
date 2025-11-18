from collections import defaultdict
from app.domain.date.check_contract_expired import is_contract_isExpired
from app.dtos.user_dto import UserReadDTO
from app.repositories import si_repository


def build_super_tree(user, perms_by_type, result, db):
    rows = si_repository.get_si_org_tree(db)

    si_map = defaultdict(lambda: {"name": "", "orgs": []})

    for row in rows:
        sid = row["si_id"]
        si_map[sid]["name"] = row["si_name"]
        si_map[sid]["logo"] = row["si_logo"]

        if row["org_id"]:
            si_map[sid]["orgs"].append(
                {
                    "id": row["org_id"],
                    "name": row["org_name"],
                    "logo": row["org_logo"],
                    "disabled": row["org_disabled"],
                    "contract_start": row["org_contract_start"],
                    "contract_end": row["org_contract_end"],
                }
            )

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
                        "id": org["id"],
                        "name": org["name"],
                        "role": "owner",
                        "isActive": not org["disabled"],
                        "logo": org["logo"],
                        "permissions": perms_by_type["org"],
                        "isExpire": (
                            is_contract_isExpired(
                                org["contract_start"], org["contract_end"]
                            )
                        ),
                    }
                    for org in data["orgs"]
                ],
            }
        )

    return {
        "user": UserReadDTO.model_validate(user),
        "permissionTree": result,
    }
