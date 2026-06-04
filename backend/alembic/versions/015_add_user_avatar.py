"""Add avatar and display_name to users.

Revision ID: 015
Revises: 014
"""
from alembic import op
import sqlalchemy as sa

revision: str = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("display_name", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "display_name")
    op.drop_column("users", "avatar")
