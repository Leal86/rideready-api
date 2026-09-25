"""adiciona timezone das atividades

Revision ID: 9eda4632668f
Revises: 384b0121d9cc
Create Date: 2026-09-25 10:55:18.844039

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9eda4632668f"
down_revision: Union[str, Sequence[str], None] = "384b0121d9cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona o timezone IANA associado ao local da atividade."""
    op.add_column(
        "activities",
        sa.Column(
            "timezone",
            sa.String(length=100),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove o timezone associado ao local da atividade."""
    op.drop_column(
        "activities",
        "timezone",
    )
