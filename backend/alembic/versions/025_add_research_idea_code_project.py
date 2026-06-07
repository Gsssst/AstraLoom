"""Add generated code project manifests to research ideas."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("research_ideas", sa.Column("generated_code_project", JSON, nullable=True))


def downgrade():
    op.drop_column("research_ideas", "generated_code_project")
