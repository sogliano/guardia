"""add case_number to cases

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS case_number_seq")

    # Add column as nullable first
    op.add_column(
        "cases",
        sa.Column(
            "case_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Backfill existing rows ordered by created_at
    op.execute(
        "UPDATE cases SET case_number = nextval('case_number_seq') "
        "WHERE case_number IS NULL"
    )

    # Set NOT NULL constraint
    op.alter_column("cases", "case_number", nullable=False)

    # Add unique constraint and index
    op.create_unique_constraint("uq_cases_case_number", "cases", ["case_number"])
    op.create_index("ix_cases_case_number", "cases", ["case_number"])

    # Set default for future inserts
    op.alter_column(
        "cases",
        "case_number",
        server_default=sa.text("nextval('case_number_seq')"),
    )


def downgrade() -> None:
    op.drop_index("ix_cases_case_number", table_name="cases")
    op.drop_constraint("uq_cases_case_number", "cases", type_="unique")
    op.drop_column("cases", "case_number")
    op.execute("DROP SEQUENCE IF EXISTS case_number_seq")
