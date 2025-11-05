def merge_org_permissions(si_map: dict):
    for _, si_entry in si_map.items():
        org_map = {}

        for org in si_entry["accessibleNode"]:
            oid = org["id"]
            if oid not in org_map:
                org_map[oid] = org
            else:
                org_map[oid]["permissions"] += org["permissions"]

        # 去重
        si_entry["accessibleNode"] = [
            {**o, "permissions": list(set(o["permissions"]))} for o in org_map.values()
        ]
