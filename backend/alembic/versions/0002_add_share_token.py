"""Migration to add share_token column to evaluations table.

Revision ID: 0002_add_share_token
Revises: 0001_initial
Create Date: 2026-07-27 04:41:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002_add_share_token'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('evaluations', sa.Column('share_token', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_evaluations_share_token'), 'evaluations', ['share_token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_evaluations_share_token'), table_name='evaluations')
    op.drop_column('evaluations', 'share_token')
