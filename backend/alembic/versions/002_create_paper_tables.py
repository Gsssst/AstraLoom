"""Create papers, categories, paper_categories tables.

Revision ID: 002
Revises: 001
Create Date: 2026-05-30
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- categories 表（自引用多级分类树）---
    op.create_table(
        "categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- papers 表 ---
    op.create_table(
        "papers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(1000), nullable=False, index=True),
        sa.Column("authors", JSON, nullable=True),
        sa.Column("year", sa.Integer(), nullable=True, index=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("doi", sa.String(500), nullable=True, unique=True),
        sa.Column("arxiv_id", sa.String(100), nullable=True, unique=True, index=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="arxiv"),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("pdf_path", sa.String(1000), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("citation_count", sa.Integer(), server_default="0"),
        sa.Column("metadata_json", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Full-text search index on title
    op.create_index("ix_papers_title_gin", "papers", ["title"])
    op.create_index("ix_papers_source", "papers", ["source"])

    # --- paper_categories 关联表 ---
    op.create_table(
        "paper_categories",
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("paper_id", "category_id", name="uq_paper_category"),
    )


def downgrade() -> None:
    op.drop_table("paper_categories")
    op.drop_table("papers")
    op.drop_table("categories")
