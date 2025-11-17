from dataclasses import dataclass


@dataclass
class OrgWriteParams:
    si_id: int
    org_id: int | None = None
    perm: str = ""


def can_write_org(access_tree: dict, params: OrgWriteParams) -> bool:
    si_id = params.si_id
    org_id = params.org_id
    perm = params.perm

    tree = access_tree.get("permissionTree", {})

    # super user 全部放行
    if tree.get("isActive") and tree.get("level") == "super":
        return True

    # iterate SI nodes
    for si_node in tree.get("accessibleNode", []):
        if si_node["id"] != si_id:
            continue

        # 找到對應的 SI（必須 active）
        if (
            si_node["id"] == si_id
            and si_node["isActive"]
            and any(
                org_node["id"] == org_id
                for org_node in si_node.get("accessibleNode", [])
            )
        ):
            return True

        # 修改 Org：檢查 Org 層級權限
        for org_node in si_node.get("accessibleNode", []):
            print(org_node)
            if org_node["id"] == org_id and org_node["isActive"]:
                print(perm, org_node.get("permissions", []))
                return perm in org_node.get("permissions", [])

    return False
