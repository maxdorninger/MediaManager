"""Add library field to Movie and Show tables

Revision ID: 1801d9f5a275
Revises: 333866afcd2c
Create Date: 2025-07-16 01:09:44.045395

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1801d9f5a275"
down_revision: Union[str, None] = "333866afcd2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "movie",
        sa.Column(
            "library", sa.String(), nullable=False, server_default=sa.text("'Default'")
        ),
    )
    op.add_column(
        "show",
        sa.Column(
            "library", sa.String(), nullable=False, server_default=sa.text("'Default'")
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("show", "library")
    op.drop_column("movie", "library")
