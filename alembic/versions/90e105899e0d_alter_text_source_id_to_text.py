"""alter text source_id to TEXT"""

from alembic import op
import sqlalchemy as sa

revision = "90e105899e0d"
down_revision = '61294d784b57'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column("text_items", "source_id", type_=sa.Text())


def downgrade():
    op.alter_column("text_items", "source_id", type_=sa.String(length=512))
