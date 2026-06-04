"""Create research idea workbench runs and enriched proposal fields."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision = "019"
down_revision = "018"


def upgrade():
    op.create_table(
        "research_idea_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("stage", sa.String(40), nullable=False, server_default="briefing"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.String(500), nullable=True),
        sa.Column("config_json", JSON, nullable=True),
        sa.Column("evidence_map", JSON, nullable=True),
        sa.Column("gap_map", JSON, nullable=True),
        sa.Column("candidate_pool", JSON, nullable=True),
        sa.Column("review_summary", JSON, nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_idea_runs_project_id", "research_idea_runs", ["project_id"])
    op.create_index("ix_research_idea_runs_project_created", "research_idea_runs", ["project_id", "created_at"])

    op.add_column("research_ideas", sa.Column("generation_run_id", UUID(as_uuid=True), nullable=True))
    op.add_column("research_ideas", sa.Column("hypothesis", sa.Text(), nullable=True))
    op.add_column("research_ideas", sa.Column("evidence_json", JSON, nullable=True))
    op.add_column("research_ideas", sa.Column("review_json", JSON, nullable=True))
    op.add_column("research_ideas", sa.Column("experiment_plan", JSON, nullable=True))
    op.create_foreign_key(
        "fk_research_ideas_generation_run_id",
        "research_ideas",
        "research_idea_runs",
        ["generation_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_research_ideas_generation_run_id", "research_ideas", ["generation_run_id"])


def downgrade():
    op.drop_index("ix_research_ideas_generation_run_id", table_name="research_ideas")
    op.drop_constraint("fk_research_ideas_generation_run_id", "research_ideas", type_="foreignkey")
    op.drop_column("research_ideas", "experiment_plan")
    op.drop_column("research_ideas", "review_json")
    op.drop_column("research_ideas", "evidence_json")
    op.drop_column("research_ideas", "hypothesis")
    op.drop_column("research_ideas", "generation_run_id")
    op.drop_index("ix_research_idea_runs_project_created", table_name="research_idea_runs")
    op.drop_index("ix_research_idea_runs_project_id", table_name="research_idea_runs")
    op.drop_table("research_idea_runs")
