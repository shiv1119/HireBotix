"""Update User Table

Revision ID: 0b1d599f6220
Revises: dfea7dfd8e10
Create Date: 2026-03-06 13:01:55.584127
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0b1d599f6220'
down_revision = 'dfea7dfd8e10'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema."""
    # Add role column as plain string with default 'USER'
    op.add_column(
        'users',
        sa.Column('role', sa.String(), nullable=False, server_default='USER')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')