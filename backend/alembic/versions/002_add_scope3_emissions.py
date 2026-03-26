"""Add Scope 3 emissions column to assets

Revision ID: 002_scope3
Revises: 001_initial
Create Date: 2026-03-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_scope3"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column("scope3_tco2e", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("assets", "scope3_tco2e")
