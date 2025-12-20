"""add imdb_id to movie and show

Revision ID: 7ceea4c15ceb
Revises: eb0bd3cc1852
Create Date: 2025-12-19
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "7ceea4c15ceb"
down_revision: Union[str, None] = "eb0bd3cc1852"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "movie",
        sa.Column("imdb_id", sa.String(), nullable=True),
    )
    op.add_column(
        "show",
        sa.Column("imdb_id", sa.String(), nullable=True),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("movie", "imdb_id")
    op.drop_column("show", "imdb_id")
