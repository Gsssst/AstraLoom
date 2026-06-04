"""Add tags to papers, create user_papers table.

Revision ID: 007
Revises: 006
Create Date: 2026-05-30
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 tags 列到 papers 表
    op.add_column("papers", sa.Column("tags", JSON, nullable=True, server_default="[]"))

    # 创建 user_papers 表（用户个人收藏、笔记）
    op.create_table(
        "user_papers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("saved", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("personal_notes", sa.Text(), nullable=True),
        sa.Column("read_status", sa.String(20), server_default="unread"),
        sa.Column("personal_tags", JSON, nullable=True, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),
    )


def downgrade() -> None:
    op.drop_table("user_papers")
    op.drop_column("papers", "tags")
