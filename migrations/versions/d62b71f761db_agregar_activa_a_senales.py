"""Agregar activa a senales

Revision ID: d62b71f761db
Revises: 12a8fce94a71
Create Date: 2026-11-08 08:56:00.788704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd62b71f761db'
down_revision: Union[str, Sequence[str], None] = '12a8fce94a71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "senales",
        sa.Column(
            "activa",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade():
    op.drop_column("senales", "activa")