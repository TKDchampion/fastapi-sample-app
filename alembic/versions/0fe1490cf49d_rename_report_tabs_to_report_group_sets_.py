"""rename report_tabs to report_group_sets and remove order column

Revision ID: 0fe1490cf49d
Revises: c96a41bded0d
Create Date: 2025-12-29 15:38:17.017216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0fe1490cf49d'
down_revision: Union[str, Sequence[str], None] = 'c96a41bded0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename report_tabs table to report_group_sets
    op.rename_table('report_tabs', 'report_group_sets')

    # Drop order column from report_group_sets (previously report_tabs)
    op.drop_column('report_group_sets', 'order')

    # Rename user_report_tab_accesses table to user_report_group_set_accesses
    op.rename_table('user_report_tab_accesses', 'user_report_group_set_accesses')

    # Rename tab_id column to report_group_set_id in user_report_group_set_accesses
    op.alter_column('user_report_group_set_accesses', 'tab_id',
                    new_column_name='report_group_set_id')

    # Update report_groups table: rename tab_id to report_group_set_id
    op.alter_column('report_groups', 'tab_id',
                    new_column_name='report_group_set_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse: rename report_group_set_id to tab_id in report_groups
    op.alter_column('report_groups', 'report_group_set_id',
                    new_column_name='tab_id')

    # Reverse: rename report_group_set_id to tab_id in user_report_group_set_accesses
    op.alter_column('user_report_group_set_accesses', 'report_group_set_id',
                    new_column_name='tab_id')

    # Reverse: rename user_report_group_set_accesses to user_report_tab_accesses
    op.rename_table('user_report_group_set_accesses', 'user_report_tab_accesses')

    # Reverse: add order column back to report_group_sets
    op.add_column('report_group_sets', sa.Column('order', sa.INTEGER(), nullable=False, server_default='0'))

    # Reverse: rename report_group_sets to report_tabs
    op.rename_table('report_group_sets', 'report_tabs')
