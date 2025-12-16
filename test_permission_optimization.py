"""
測試權限查詢優化

這個腳本驗證快速路徑（精確查詢）和慢速路徑（權限樹）產生相同的結果
"""

import sys
import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repositories import user_repository
from app.services.user_service import get_user_access_tree
from app.domain.access_tree.check_user_access import OrgWriteParamsDTO, can_write_org


def test_permission_query_comparison():
    """比較快速路徑和慢速路徑的結果是否一致"""
    db: Session = SessionLocal()

    try:
        # 獲取測試用戶（請根據實際數據調整）
        users = user_repository.get_all_users(db)
        if not users:
            print("❌ 沒有找到測試用戶")
            return

        user = users[0]
        print(f"✓ 測試用戶: {user.email} (ID: {user.id})")

        # 測試案例
        test_cases = [
            # (si_id, org_id, perm, description)
            (1, None, "", "檢查 SI 層級權限"),
            (1, 1, "pass", "檢查 Org 存在（pass）"),
            (1, 1, "org.edit", "檢查特定權限"),
            (1, 1, "member.view", "檢查成員查看權限"),
        ]

        results_match = True
        for si_id, org_id, perm, description in test_cases:
            print(f"\n測試: {description}")
            print(f"  參數: si_id={si_id}, org_id={org_id}, perm='{perm}'")

            params = OrgWriteParamsDTO(si_id=si_id, org_id=org_id, perm=perm)

            # 快速路徑
            start_fast = time.perf_counter()
            try:
                fast_result = user_repository.check_user_has_permission_fast(
                    db, user.id, si_id, org_id, perm
                )
                fast_time = (time.perf_counter() - start_fast) * 1000  # ms
            except Exception as e:
                print(f"  ❌ 快速路徑錯誤: {e}")
                fast_result = False
                fast_time = 0

            # 慢速路徑
            start_slow = time.perf_counter()
            try:
                access_tree = get_user_access_tree(db, user)
                slow_result = can_write_org(access_tree, params)
                slow_time = (time.perf_counter() - start_slow) * 1000  # ms
            except Exception as e:
                print(f"  ❌ 慢速路徑錯誤: {e}")
                slow_result = False
                slow_time = 0

            # 比較結果
            match = "✓" if fast_result == slow_result else "❌"
            print(f"  {match} 快速路徑: {fast_result} ({fast_time:.2f}ms)")
            print(f"  {match} 慢速路徑: {slow_result} ({slow_time:.2f}ms)")

            if fast_time > 0 and slow_time > 0:
                speedup = slow_time / fast_time
                print(f"  ⚡ 效能提升: {speedup:.1f}x")

            if fast_result != slow_result:
                print(f"  ⚠️  結果不一致！")
                results_match = False

        print("\n" + "=" * 60)
        if results_match:
            print("✓ 所有測試通過！快速路徑和慢速路徑結果一致")
        else:
            print("❌ 測試失敗：快速路徑和慢速路徑結果不一致")

    except Exception as e:
        print(f"❌ 測試過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("開始權限查詢優化測試...")
    print("=" * 60)
    test_permission_query_comparison()
