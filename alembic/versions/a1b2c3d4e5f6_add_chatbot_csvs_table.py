"""add chatbot_csvs table

Revision ID: a1b2c3d4e5f6
Revises: f0ad3179786b
Create Date: 2026-04-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "2fc3be3ea34b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chatbot_csvs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chatbot_id", sa.Integer(), nullable=False),
        sa.Column("gcs_url", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chatbot_id"], ["chatbots.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chatbot_csvs_chatbot_id", "chatbot_csvs", ["chatbot_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_chatbot_csvs_chatbot_id", table_name="chatbot_csvs")
    op.drop_table("chatbot_csvs")
