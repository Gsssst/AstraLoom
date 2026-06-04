"""Add personal annotations to user papers."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = "021"
down_revision = "020"


def upgrade():
    op.add_column("user_papers", sa.Column("personal_annotations", JSON, nullable=True))


def downgrade():
    op.drop_column("user_papers", "personal_annotations")
