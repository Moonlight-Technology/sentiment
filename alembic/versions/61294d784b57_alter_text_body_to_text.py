"""alter text body to TEXT"""

from alembic import op
import sqlalchemy as sa

revision = "61294d784b57"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("text_items", "body", type_=sa.Text())


def downgrade():
    op.alter_column("text_items", "body", type_=sa.String(length=512))
