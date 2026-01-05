"""add original_language columns to show and movie tables

Revision ID: 16e78af9e5bf
Revises: eb0bd3cc1852
Create Date: 2025-12-13 18:47:02.146038

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "16e78af9e5bf"
down_revision: Union[str, None] = "eb0bd3cc1852"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add original_language column to show table
    op.add_column("show", sa.Column("original_language", sa.String(10), nullable=True))

    # Add original_language column to movie table
    op.add_column("movie", sa.Column("original_language", sa.String(10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove original_language column from movie table
    op.drop_column("movie", "original_language")

    # Remove original_language column from show table
    op.drop_column("show", "original_language")
