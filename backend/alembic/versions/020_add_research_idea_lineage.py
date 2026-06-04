"""Add proposal lineage fields for research idea evolution."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision = "020"
down_revision = "019"


def upgrade():
    op.add_column("research_ideas", sa.Column("parent_idea_id", UUID(as_uuid=True), nullable=True))
    op.add_column("research_ideas", sa.Column("evolution_json", JSON, nullable=True))
    op.create_foreign_key(
        "fk_research_ideas_parent_idea_id",
        "research_ideas",
        "research_ideas",
        ["parent_idea_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_research_ideas_parent_idea_id", "research_ideas", ["parent_idea_id"])


def downgrade():
    op.drop_index("ix_research_ideas_parent_idea_id", table_name="research_ideas")
    op.drop_constraint("fk_research_ideas_parent_idea_id", "research_ideas", type_="foreignkey")
    op.drop_column("research_ideas", "evolution_json")
    op.drop_column("research_ideas", "parent_idea_id")
