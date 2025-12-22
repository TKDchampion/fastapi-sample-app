from dataclasses import dataclass


@dataclass
class PermissionCheckParams:
    si_id: int
    org_id: int | None = None
    perm: str = ""


def can_write_org(access_tree: dict, params: PermissionCheckParams) -> bool:
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

        if org_id:
            # 找到對應的 SI（必須 active）
            if (
                si_node["id"] == si_id
                and si_node["isActive"]
                and any(
                    org_node["id"] == org_id and org_node.get("isContractLive", True)
                    for org_node in si_node.get("accessibleNode", [])
                )
            ):
                return True
        else:
            if si_node["id"] == si_id and si_node["isActive"]:
                return True

        # 修改 Org：檢查 Org 層級權限
        for org_node in si_node.get("accessibleNode", []):
            if (
                org_node["id"] == org_id
                and org_node["isActive"]
                and org_node.get("isContractLive", True)
            ):
                # 如果 perm 是 "pass"，繞過權限檢查，只驗證基本條件
                if perm == "pass":
                    return True
                return perm in org_node.get("permissions", [])

    return False
