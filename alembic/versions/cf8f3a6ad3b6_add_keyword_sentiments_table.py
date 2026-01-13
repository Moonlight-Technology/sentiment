"""add keyword sentiments table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "cf8f3a6ad3b6"
down_revision = "1b5a2cc3d3f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "keyword_sentiments",
        sa.Column("keyword", sa.String(length=128), primary_key=True),
        sa.Column("positive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("neutral_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("negative_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("keyword_sentiments")
