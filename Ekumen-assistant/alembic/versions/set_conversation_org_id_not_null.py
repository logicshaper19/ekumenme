"""
Set conversations.organization_id to NOT NULL after backfill

Revision ID: set_conversation_org_id_not_null
Revises: backfill_conversation_org_id
Create Date: 2025-10-02 00:20:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'set_conversation_org_id_not_null'
down_revision = 'backfill_conversation_org_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Ensure there are no NULL organization_id values remaining
    null_count = conn.execute(sa.text("SELECT COUNT(*) FROM conversations WHERE organization_id IS NULL")).scalar()
    if null_count and int(null_count) > 0:
        raise RuntimeError(f"Cannot set NOT NULL: {null_count} conversations have NULL organization_id. Backfill or fix data first.")

    op.alter_column(
        'conversations',
        'organization_id',
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        'conversations',
        'organization_id',
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True
    )

