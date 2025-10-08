"""add_is_answered_to_questions

Revision ID: aba759167d5b
Revises: 628c7129289e
Create Date: 2025-10-09 01:08:13.981675

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aba759167d5b'
down_revision = '628c7129289e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_answered column to questions table
    op.add_column('questions', sa.Column('is_answered', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove is_answered column from questions table
    op.drop_column('questions', 'is_answered')