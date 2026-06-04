"""Create workspace resources and activities."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision = "022"
down_revision = "021"


def upgrade():
    op.create_table(
        "project_space_resources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("project_spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("added_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", JSON, nullable=True),
        sa.UniqueConstraint("space_id", "resource_type", "resource_id", name="uq_project_space_resource"),
    )
    op.create_index("ix_project_space_resources_id", "project_space_resources", ["id"])
    op.create_index("ix_project_space_resources_space_id", "project_space_resources", ["space_id"])
    op.create_index("ix_project_space_resources_resource_type", "project_space_resources", ["resource_type"])
    op.create_index("ix_project_space_resources_resource_id", "project_space_resources", ["resource_id"])
    op.create_index("ix_project_space_resources_added_by", "project_space_resources", ["added_by"])
    op.create_index("ix_project_space_resources_space_type", "project_space_resources", ["space_id", "resource_type"])

    op.create_table(
        "project_space_activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("project_spaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", sa.String(length=80), nullable=True),
        sa.Column("metadata_json", JSON, nullable=True),
    )
    op.create_index("ix_project_space_activities_id", "project_space_activities", ["id"])
    op.create_index("ix_project_space_activities_space_id", "project_space_activities", ["space_id"])
    op.create_index("ix_project_space_activities_actor_id", "project_space_activities", ["actor_id"])
    op.create_index("ix_project_space_activities_action", "project_space_activities", ["action"])
    op.create_index("ix_project_space_activities_resource_type", "project_space_activities", ["resource_type"])
    op.create_index("ix_project_space_activities_resource_id", "project_space_activities", ["resource_id"])
    op.create_index("ix_project_space_activities_space_created", "project_space_activities", ["space_id", "created_at"])
    op.create_index("ix_project_space_activities_actor_created", "project_space_activities", ["actor_id", "created_at"])


def downgrade():
    op.drop_table("project_space_activities")
    op.drop_table("project_space_resources")
