from app.domain.date.check_contract_expired import is_contract_isExpired
from app.repositories import org_repository


def fill_si_full_access(si_map: dict, perms_by_type, db):
    full_si_ids = [
        sid for sid, v in si_map.items() if v["permissions"] == perms_by_type["si"]
    ]

    if not full_si_ids:
        return

    orgs_all = org_repository.get_all_orgs(db)

    for org in orgs_all:
        if org.si_id in full_si_ids:
            exists = {o["id"] for o in si_map[org.si_id]["accessibleNode"]}
            if org.id not in exists:
                si_map[org.si_id]["accessibleNode"].append(
                    {
                        "level": "org",
                        "id": org.id,
                        "name": org.name,
                        "role": "owner",
                        "logo": org.logo,
                        "isActive": not org.disabled,
                        "permissions": [p for p in perms_by_type["org"] if p],
                        "isContractLive": is_contract_isExpired(
                            org.contract_start, org.contract_end
                        ),
                    }
                )
