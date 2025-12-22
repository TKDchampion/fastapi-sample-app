"""add_indexes_for_permission_queries

Revision ID: 8cf6334b357d
Revises: f0ad3179786b
Create Date: 2025-12-16 15:44:32.473535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cf6334b357d'
down_revision: Union[str, Sequence[str], None] = 'f0ad3179786b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add indexes for optimized permission queries."""

    # 優化 user_roles 表的查詢
    # 用於快速查找用戶的權限範圍（super/si/org）
    op.create_index(
        'idx_user_roles_user_scope',
        'user_roles',
        ['user_id', 'scope_type', 'scope_id'],
        unique=False
    )

    # 優化 role_permissions 表的查詢
    # 用於快速查找角色的權限
    op.create_index(
        'idx_role_permissions_role',
        'role_permissions',
        ['role_id', 'permission_id'],
        unique=False
    )

    # 優化 organizations 表的查詢
    # 用於快速檢查 contract 有效性和 disabled 狀態
    op.create_index(
        'idx_organizations_si_active',
        'organizations',
        ['si_id', 'disabled'],
        unique=False
    )

    # 優化 si 表的查詢
    # 用於快速檢查 SI 的 disabled 狀態
    op.create_index(
        'idx_si_disabled',
        'si',
        ['disabled'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema: Remove indexes."""

    op.drop_index('idx_si_disabled', table_name='si')
    op.drop_index('idx_organizations_si_active', table_name='organizations')
    op.drop_index('idx_role_permissions_role', table_name='role_permissions')
    op.drop_index('idx_user_roles_user_scope', table_name='user_roles')
