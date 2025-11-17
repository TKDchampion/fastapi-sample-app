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
        # 找到對應的 SI（必須 active）
        if si_node["id"] == si_id and si_node["isActive"]:
            return True
        if si_node["id"] != si_id or not si_node["isActive"]:
            continue

        # 新增 Org：檢查 SI 層級權限
        # if org_id is None:
        #     return perm in si_node.get("permissions", [])

        # 修改 Org：檢查 Org 層級權限
        for org_node in si_node.get("accessibleNode", []):
            if org_node["id"] == org_id and org_node["isActive"]:
                return perm in org_node.get("permissions", [])

    return False
