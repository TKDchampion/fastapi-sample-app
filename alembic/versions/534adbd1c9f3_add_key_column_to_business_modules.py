"""add key column to business_modules

Revision ID: 534adbd1c9f3
Revises: 29901f2f2ea9
Create Date: 2026-02-03 10:12:27.331496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '534adbd1c9f3'
down_revision: Union[str, Sequence[str], None] = '29901f2f2ea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 先加入可為 null 的欄位
    op.add_column('business_modules', sa.Column('key', sa.String(), nullable=True))

    # 將現有數據的 key 設為 name（之後需手動調整）
    op.execute("UPDATE business_modules SET key = name WHERE key IS NULL")

    # 改為 NOT NULL
    op.alter_column('business_modules', 'key', nullable=False)

    # 加入 unique constraint
    op.create_unique_constraint('uq_business_modules_key', 'business_modules', ['key'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_business_modules_key', 'business_modules', type_='unique')
    op.drop_column('business_modules', 'key')
