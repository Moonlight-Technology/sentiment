"""Initial ingestion + sentiment tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "text_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=512), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
    )
    op.create_unique_constraint("uq_text_items_source_id", "text_items", ["source_id"])

    op.create_table(
        "sentiment_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("text_item_id", sa.String(length=36), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("pipeline_stage", sa.String(length=32), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("scores_by_label", sa.JSON(), nullable=True),
        sa.Column("explanations", sa.JSON(), nullable=True),
        sa.Column("annotations", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["text_item_id"], ["text_items.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sentiment_results_text_item_id", "sentiment_results", ["text_item_id"])


def downgrade() -> None:
    op.drop_index("ix_sentiment_results_text_item_id", table_name="sentiment_results")
    op.drop_table("sentiment_results")
    op.drop_constraint("uq_text_items_source_id", "text_items", type_="unique")
    op.drop_table("text_items")
