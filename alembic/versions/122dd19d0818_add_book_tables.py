"""add book tables

Revision ID: 122dd19d0818
Revises: 6679fc11aa8f
Create Date: 2026-02-08 14:17:34.994940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import fastapi_users_db_sqlalchemy.generics


# revision identifiers, used by Alembic.
revision: str = "122dd19d0818"
down_revision: Union[str, None] = "6679fc11aa8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reference the existing quality enum - use postgresql.ENUM to avoid recreation
quality_enum = postgresql.ENUM("uhd", "fullhd", "hd", "sd", "unknown", name="quality", create_type=False)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table("book_author",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("metadata_provider", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("overview", sa.String(), nullable=False),
        sa.Column("library", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", "metadata_provider")
    )
    op.create_table("book",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(), nullable=False),
        sa.Column("isbn", sa.String(), nullable=True),
        sa.Column("publisher", sa.String(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["book_author.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("author_id", "external_id")
    )
    op.create_table("book_file",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("torrent_id", sa.Uuid(), nullable=True),
        sa.Column("file_path_suffix", sa.String(), nullable=False),
        sa.Column("quality", quality_enum, nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["torrent_id"], ["torrent.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("book_id", "file_path_suffix")
    )
    op.create_table("book_request",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("wanted_quality", quality_enum, nullable=False),
        sa.Column("min_quality", quality_enum, nullable=False),
        sa.Column("requested_by_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("authorized", sa.Boolean(), nullable=False),
        sa.Column("authorized_by_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.ForeignKeyConstraint(["authorized_by_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["book_id"], ["book.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "wanted_quality")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("book_request")
    op.drop_table("book_file")
    op.drop_table("book")
    op.drop_table("book_author")
