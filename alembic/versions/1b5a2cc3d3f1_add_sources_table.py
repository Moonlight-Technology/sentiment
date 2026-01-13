"""add sources table"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "1b5a2cc3d3f1"
down_revision = "90e105899e0d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("schedule", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="inactive"),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    sources_table = sa.table(
        "sources",
        sa.Column("id", sa.String(length=36)),
        sa.Column("name", sa.String(length=128)),
        sa.Column("type", sa.String(length=32)),
        sa.Column("config", sa.JSON()),
        sa.Column("schedule", sa.String(length=32)),
        sa.Column("status", sa.String(length=32)),
        sa.Column("last_run", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.utcnow()
    op.bulk_insert(
        sources_table,
        [
            {
                "id": str(uuid4()),
                "name": "Default RSS",
                "type": "rss",
                "config": {"url": "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id"},
                "schedule": "daily",
                "status": "active",
                "last_run": now,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("sources")
