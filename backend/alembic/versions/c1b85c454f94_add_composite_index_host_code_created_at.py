"""add_composite_index_host_code_created_at

Revision ID: c1b85c454f94
Revises: 9372cec8298d
Create Date: 2025-10-08 20:52:27.327572

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1b85c454f94'
down_revision = '9372cec8298d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create composite index for efficient host_code + created_at queries
    # This improves performance for GET /api/v1/events/host/{host_code} with pagination
    op.create_index(
        'idx_host_event_created',
        'events',
        ['host_code', sa.text('created_at DESC')],
        unique=False
    )


def downgrade() -> None:
    # Drop the composite index
    op.drop_index('idx_host_event_created', table_name='events')