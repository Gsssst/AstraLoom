"""Create writing project tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "018"
down_revision = "017"


def upgrade():
    # WritingProject
    op.create_table(
        "writing_projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_type", sa.String(50), nullable=False, server_default="blank"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_writing_projects_user_status", "writing_projects", ["user_id", "status"])

    # WritingSection
    op.create_table(
        "writing_sections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("writing_projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_writing_sections_project_order", "writing_sections", ["project_id", "order"])

    # PolishVersion
    op.create_table(
        "polish_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("section_id", UUID(as_uuid=True), sa.ForeignKey("writing_sections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("polished_text", sa.Text(), nullable=False),
        sa.Column("diff_json", sa.JSON(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("user_actions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_polish_versions_section_version", "polish_versions", ["section_id", "version_number"])


def downgrade():
    op.drop_table("polish_versions")
    op.drop_table("writing_sections")
    op.drop_table("writing_projects")
