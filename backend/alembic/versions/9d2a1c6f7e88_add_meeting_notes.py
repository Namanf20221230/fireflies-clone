"""add persistent meeting notes

Revision ID: 9d2a1c6f7e88
Revises: 4513a2e5989a
"""

from alembic import op
import sqlalchemy as sa
from app.models.types import UTCDateTime

revision = "9d2a1c6f7e88"
down_revision = "4513a2e5989a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meeting_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meeting_notes_meeting_id", "meeting_notes", ["meeting_id"])


def downgrade() -> None:
    op.drop_index("ix_meeting_notes_meeting_id", table_name="meeting_notes")
    op.drop_table("meeting_notes")
