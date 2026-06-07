"""Create workspace feedback issues."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_space_issues",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("project_spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("creator_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignee_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("closed_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("issue_type", sa.String(length=40), nullable=False, server_default="feedback"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("labels", JSON, nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", JSON, nullable=True),
    )
    op.create_index("ix_project_space_issues_id", "project_space_issues", ["id"])
    op.create_index("ix_project_space_issues_space_id", "project_space_issues", ["space_id"])
    op.create_index("ix_project_space_issues_creator_id", "project_space_issues", ["creator_id"])
    op.create_index("ix_project_space_issues_assignee_id", "project_space_issues", ["assignee_id"])
    op.create_index("ix_project_space_issues_closed_by_id", "project_space_issues", ["closed_by_id"])
    op.create_index("ix_project_space_issues_status", "project_space_issues", ["status"])
    op.create_index("ix_project_space_issues_issue_type", "project_space_issues", ["issue_type"])
    op.create_index("ix_project_space_issues_priority", "project_space_issues", ["priority"])
    op.create_index("ix_project_space_issues_space_status", "project_space_issues", ["space_id", "status"])
    op.create_index("ix_project_space_issues_space_priority", "project_space_issues", ["space_id", "priority"])
    op.create_index("ix_project_space_issues_space_created", "project_space_issues", ["space_id", "created_at"])

    op.create_table(
        "project_space_issue_comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("issue_id", UUID(as_uuid=True), sa.ForeignKey("project_space_issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_project_space_issue_comments_id", "project_space_issue_comments", ["id"])
    op.create_index("ix_project_space_issue_comments_issue_id", "project_space_issue_comments", ["issue_id"])
    op.create_index("ix_project_space_issue_comments_author_id", "project_space_issue_comments", ["author_id"])
    op.create_index("ix_project_space_issue_comments_issue_created", "project_space_issue_comments", ["issue_id", "created_at"])


def downgrade():
    op.drop_table("project_space_issue_comments")
    op.drop_table("project_space_issues")
