"""Add paper_chat_history to user_papers.

Revision ID: 009
Revises: 008
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_papers", sa.Column("paper_chat_history", JSON, nullable=True, server_default="[]"))


def downgrade() -> None:
    op.drop_column("user_papers", "paper_chat_history")
