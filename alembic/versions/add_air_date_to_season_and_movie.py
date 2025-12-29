"""Add air_date to Season and Movie tables

Revision ID: f1a2b3c4d5e6
Revises: eb0bd3cc1852
Create Date: 2025-11-02 21:49:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "eb0bd3cc1852"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "season",
        sa.Column("air_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "movie",
        sa.Column("air_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("season", "air_date")
    op.drop_column("movie", "air_date")
