"""create episode file table and add episode column to indexerqueryresult

Revision ID: 3a8fbd71e2c2
Revises: 9f3c1b2a4d8e
Create Date: 2026-01-08 13:43:00

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a8fbd71e2c2"
down_revision: Union[str, None] = "9f3c1b2a4d8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    quality_enum = postgresql.ENUM("uhd", "fullhd", "hd", "sd", "unknown", name="quality",
        create_type=False,
    )
    # Create episode file table
    op.create_table(
        "episode_file",
        sa.Column("episode_id", sa.UUID(), nullable=False),
        sa.Column("torrent_id", sa.UUID(), nullable=True),
        sa.Column("file_path_suffix", sa.String(), nullable=False),
        sa.Column("quality", quality_enum, nullable=False),
        sa.ForeignKeyConstraint(["episode_id"], ["episode.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["torrent_id"], ["torrent.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("episode_id", "file_path_suffix"),
    )
    # Add episode column to indexerqueryresult
    op.add_column(
        "indexer_query_result", sa.Column("episode", postgresql.ARRAY(sa.Integer()), nullable=True),
    )

def downgrade() -> None:
    op.drop_table("episode_file")
    op.drop_column("indexer_query_result", "episode")