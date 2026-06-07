"""Create research code project version snapshots."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "research_code_project_versions",
        sa.Column("idea_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("project_name", sa.String(length=300), nullable=False),
        sa.Column("framework", sa.String(length=80), nullable=False, server_default="pytorch"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("project_manifest", JSON(), nullable=False),
        sa.Column("representative_code", sa.Text(), nullable=True),
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["research_ideas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idea_id", "version", name="uq_research_code_project_version"),
    )
    op.create_index(op.f("ix_research_code_project_versions_id"), "research_code_project_versions", ["id"], unique=False)
    op.create_index(op.f("ix_research_code_project_versions_idea_id"), "research_code_project_versions", ["idea_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_research_code_project_versions_idea_id"), table_name="research_code_project_versions")
    op.drop_index(op.f("ix_research_code_project_versions_id"), table_name="research_code_project_versions")
    op.drop_table("research_code_project_versions")
