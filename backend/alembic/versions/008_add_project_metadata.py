"""Add metadata_json to research_projects.

Revision ID: 008
Revises: 007
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("research_projects", sa.Column("metadata_json", JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("research_projects", "metadata_json")
