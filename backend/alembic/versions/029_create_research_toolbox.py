"""Create research toolbox tables.

Revision ID: 029
Revises: 028
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_tools",
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("use_cases", sa.Text(), nullable=True),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("maturity", sa.String(length=30), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_tools_id"), "research_tools", ["id"], unique=False)
    op.create_index(op.f("ix_research_tools_kind"), "research_tools", ["kind"], unique=False)
    op.create_index(op.f("ix_research_tools_maturity"), "research_tools", ["maturity"], unique=False)
    op.create_index(op.f("ix_research_tools_name"), "research_tools", ["name"], unique=False)
    op.create_index("ix_research_tools_name_kind", "research_tools", ["name", "kind"], unique=False)
    op.create_index(op.f("ix_research_tools_created_by_user_id"), "research_tools", ["created_by_user_id"], unique=False)

    op.create_table(
        "research_tool_papers",
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation", sa.String(length=40), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["research_tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tool_id", "paper_id", name="uq_research_tool_paper"),
    )
    op.create_index(op.f("ix_research_tool_papers_id"), "research_tool_papers", ["id"], unique=False)
    op.create_index(op.f("ix_research_tool_papers_paper_id"), "research_tool_papers", ["paper_id"], unique=False)
    op.create_index(op.f("ix_research_tool_papers_relation"), "research_tool_papers", ["relation"], unique=False)
    op.create_index(op.f("ix_research_tool_papers_tool_id"), "research_tool_papers", ["tool_id"], unique=False)
    op.create_index(
        op.f("ix_research_tool_papers_created_by_user_id"),
        "research_tool_papers",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index("ix_research_tool_papers_tool_relation", "research_tool_papers", ["tool_id", "relation"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_research_tool_papers_tool_relation", table_name="research_tool_papers")
    op.drop_index(op.f("ix_research_tool_papers_created_by_user_id"), table_name="research_tool_papers")
    op.drop_index(op.f("ix_research_tool_papers_tool_id"), table_name="research_tool_papers")
    op.drop_index(op.f("ix_research_tool_papers_relation"), table_name="research_tool_papers")
    op.drop_index(op.f("ix_research_tool_papers_paper_id"), table_name="research_tool_papers")
    op.drop_index(op.f("ix_research_tool_papers_id"), table_name="research_tool_papers")
    op.drop_table("research_tool_papers")

    op.drop_index(op.f("ix_research_tools_created_by_user_id"), table_name="research_tools")
    op.drop_index("ix_research_tools_name_kind", table_name="research_tools")
    op.drop_index(op.f("ix_research_tools_name"), table_name="research_tools")
    op.drop_index(op.f("ix_research_tools_maturity"), table_name="research_tools")
    op.drop_index(op.f("ix_research_tools_kind"), table_name="research_tools")
    op.drop_index(op.f("ix_research_tools_id"), table_name="research_tools")
    op.drop_table("research_tools")
