"""Create workspace resources and activities."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision = "022"
down_revision = "021"


def upgrade():
    bind = op.get_bind()
    existing_tables = set(sa.inspect(bind).get_table_names())

    if "project_spaces" not in existing_tables:
        op.create_table(
            "project_spaces",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("metadata_json", JSON, nullable=True),
        )
        op.create_index("ix_project_spaces_id", "project_spaces", ["id"])
        op.create_index("ix_project_spaces_owner_id", "project_spaces", ["owner_id"])
        op.create_index("ix_project_spaces_owner_status", "project_spaces", ["owner_id", "status"])

    if "project_space_members" not in existing_tables:
        op.create_table(
            "project_space_members",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("space_id", UUID(as_uuid=True), sa.ForeignKey("project_spaces.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False, server_default="viewer"),
            sa.UniqueConstraint("space_id", "user_id", name="uq_project_space_member"),
        )
        op.create_index("ix_project_space_members_id", "project_space_members", ["id"])
        op.create_index("ix_project_space_members_space_id", "project_space_members", ["space_id"])
        op.create_index("ix_project_space_members_user_id", "project_space_members", ["user_id"])
        op.create_index("ix_project_space_members_user_role", "project_space_members", ["user_id", "role"])

    if "project_space_resources" not in existing_tables:
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

    if "project_space_activities" not in existing_tables:
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
    op.drop_table("project_space_members")
    op.drop_table("project_spaces")
