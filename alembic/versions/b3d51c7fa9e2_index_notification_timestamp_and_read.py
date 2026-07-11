"""index notification timestamp and read

Revision ID: b3d51c7fa9e2
Revises: e60ae827ed98
Create Date: 2026-07-11 10:12:38.114905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3d51c7fa9e2'
down_revision: Union[str, None] = 'e60ae827ed98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The notification list is ordered by timestamp descending and paginated,
    # so the index matches that order to keep a page from sorting the table.
    op.create_index(
        'ix_notification_timestamp_desc',
        'notification',
        [sa.text('timestamp DESC')],
        unique=False,
    )
    # Unread notifications are a small fraction of the table, so a partial
    # index keeps the unread query off a full table scan.
    op.create_index(
        'ix_notification_unread_timestamp_desc',
        'notification',
        [sa.text('timestamp DESC')],
        unique=False,
        postgresql_where=sa.text('read = false'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_notification_unread_timestamp_desc', table_name='notification')
    op.drop_index('ix_notification_timestamp_desc', table_name='notification')
