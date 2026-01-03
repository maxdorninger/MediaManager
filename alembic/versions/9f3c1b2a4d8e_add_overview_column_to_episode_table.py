"""add overview column to episode table

Revision ID: 9f3c1b2a4d8e
Revises: 2c61f662ca9e
Create Date: 2025-12-29 21:45:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f3c1b2a4d8e"
down_revision: Union[str, None] = "2c61f662ca9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add overview to episode table
    op.add_column(
        "episode",
        sa.Column("overview", sa.Text(), nullable=True),
    )

def downgrade() -> None:
    op.drop_column("episode", "overview")

