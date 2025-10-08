"""remove_question_status_column

Revision ID: 628c7129289e
Revises: afc106c8cd16
Create Date: 2025-10-08 23:17:15.844932

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '628c7129289e'
down_revision = 'afc106c8cd16'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the status column from questions table
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_column('status')


def downgrade() -> None:
    # Add the status column back if we need to rollback
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(), nullable=False, server_default='submitted'))
