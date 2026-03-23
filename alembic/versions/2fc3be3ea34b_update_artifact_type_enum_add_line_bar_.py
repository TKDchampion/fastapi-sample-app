"""update artifact type enum add line bar pie

Revision ID: 2fc3be3ea34b
Revises: cc58f4b95eee
Create Date: 2026-03-23 15:00:28.562733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fc3be3ea34b'
down_revision: Union[str, Sequence[str], None] = 'cc58f4b95eee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # PostgreSQL does not support removing enum values; recreate the enum.
    op.execute("ALTER TYPE artifacttype RENAME TO artifacttype_old")
    op.execute("CREATE TYPE artifacttype AS ENUM ('line', 'bar', 'pie', 'table', 'image', 'file', 'code', 'json_schema')")
    op.execute(
        "ALTER TABLE artifacts ALTER COLUMN type TYPE artifacttype "
        "USING type::text::artifacttype"
    )
    op.execute("DROP TYPE artifacttype_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE artifacttype RENAME TO artifacttype_old")
    op.execute("CREATE TYPE artifacttype AS ENUM ('chart', 'table', 'image', 'file', 'code', 'json_schema')")
    op.execute(
        "ALTER TABLE artifacts ALTER COLUMN type TYPE artifacttype "
        "USING type::text::artifacttype"
    )
    op.execute("DROP TYPE artifacttype_old")
