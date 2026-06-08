"""Add paper import owner metadata.

Revision ID: 027
Revises: 026
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("papers", sa.Column("imported_by_user_id", UUID(as_uuid=True), nullable=True))
    op.add_column("papers", sa.Column("imported_by_username", sa.String(length=100), nullable=True))
    op.create_index("ix_papers_imported_by_user_id", "papers", ["imported_by_user_id"])
    op.create_index("ix_papers_imported_by_username", "papers", ["imported_by_username"])
    op.create_foreign_key(
        "fk_papers_imported_by_user_id",
        "papers",
        "users",
        ["imported_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("UPDATE papers SET imported_by_username = 'gst' WHERE imported_by_username IS NULL")


def downgrade() -> None:
    op.drop_constraint("fk_papers_imported_by_user_id", "papers", type_="foreignkey")
    op.drop_index("ix_papers_imported_by_username", table_name="papers")
    op.drop_index("ix_papers_imported_by_user_id", table_name="papers")
    op.drop_column("papers", "imported_by_username")
    op.drop_column("papers", "imported_by_user_id")
