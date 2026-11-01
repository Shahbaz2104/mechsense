"""add live reading source

Revision ID: b3f1c0d24e88
Revises: 7a58f7b51dfd
Create Date: 2026-10-14 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3f1c0d24e88'
down_revision: Union[str, Sequence[str], None] = '7a58f7b51dfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE reading_source ADD VALUE IF NOT EXISTS 'live'")


def downgrade() -> None:
    """Downgrade schema.

    PostgreSQL does not support removing values from an enum type; the 'live'
    value is left in place (it becomes unused).
    """
