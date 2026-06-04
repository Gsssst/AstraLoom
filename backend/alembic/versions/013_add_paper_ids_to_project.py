"""Add paper_ids to research_projects.

Revision ID: 013
Revises: 012
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("research_projects", sa.Column("paper_ids", JSON, nullable=True, server_default="[]"))


def downgrade() -> None:
    op.drop_column("research_projects", "paper_ids")
