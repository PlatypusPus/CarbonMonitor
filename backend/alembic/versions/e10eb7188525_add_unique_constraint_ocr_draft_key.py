"""add_unique_constraint_ocr_draft_key

Revision ID: e10eb7188525
Revises: 93cd4e11117a
Create Date: 2026-09-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e10eb7188525'
down_revision: Union[str, Sequence[str], None] = '93cd4e11117a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint for idempotent draft key
    op.create_unique_constraint(
        "uq_ocr_draft_key",
        "ocr_drafts",
        [
            "facility_id",
            "period_start",
            "period_end",
            "activity_type",
            "quantity",
            "unit",
            "source_type",
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_ocr_draft_key", "ocr_drafts", type_="unique")