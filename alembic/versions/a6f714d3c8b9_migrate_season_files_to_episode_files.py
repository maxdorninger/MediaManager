"""migrate season files to episode files and drop the legacy table

Revision ID: a6f714d3c8b9
Revises: 16e78af9e5bf
Create Date: 2026-02-22 16:30:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a6f714d3c8b9"
down_revision: Union[str, None] = "3a8fbd71e2c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Copy season_file records into episode_file and remove the legacy table."""
    op.execute(
        """
        INSERT INTO episode_file (episode_id, torrent_id, file_path_suffix, quality)
        SELECT episode.id, season_file.torrent_id, season_file.file_path_suffix, season_file.quality
        FROM season_file
        JOIN season ON season.id = season_file.season_id
        JOIN episode ON episode.season_id = season.id
        LEFT JOIN episode_file ON
            episode_file.episode_id = episode.id
            AND episode_file.file_path_suffix = season_file.file_path_suffix
        WHERE episode_file.episode_id IS NULL
        """
    )
    op.drop_table("season_file")


def downgrade() -> None:
    """Recreate season_file, repopulate it from episode_file, and keep both tables."""
    quality_enum = postgresql.ENUM(
        "uhd", "fullhd", "hd", "sd", "unknown", name="quality", create_type=False
    )

    op.create_table(
        "season_file",
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("torrent_id", sa.UUID(), nullable=True),
        sa.Column("file_path_suffix", sa.String(), nullable=False),
        sa.Column("quality", quality_enum, nullable=False),
        sa.ForeignKeyConstraint(["season_id"], ["season.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["torrent_id"], ["torrent.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("season_id", "file_path_suffix"),
    )

    op.execute(
        """
        INSERT INTO season_file (season_id, torrent_id, file_path_suffix, quality)
        SELECT DISTINCT ON (episode.season_id, episode_file.file_path_suffix)
            episode.season_id,
            episode_file.torrent_id,
            episode_file.file_path_suffix,
            episode_file.quality
        FROM episode_file
        JOIN episode ON episode.id = episode_file.episode_id
        ORDER BY episode.season_id, episode_file.file_path_suffix, episode_file.torrent_id, episode_file.quality
        """
    )

