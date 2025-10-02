"""
Backfill conversations.organization_id where users have a single active org membership

Revision ID: backfill_conversation_org_id
Revises: add_conversation_organization_id
Create Date: 2025-10-02 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'backfill_conversation_org_id'
down_revision = 'add_conversation_organization_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use a SQL statement to backfill only for users with a single active membership
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        UPDATE conversations c
        SET organization_id = m.organization_id
        FROM (
            SELECT om.user_id, om.organization_id
            FROM organization_memberships om
            JOIN organizations o ON o.id = om.organization_id
            WHERE om.is_active = TRUE AND o.status = 'active'
            GROUP BY om.user_id, om.organization_id
            HAVING COUNT(*) = 1
        ) AS m
        WHERE c.user_id = m.user_id
          AND c.organization_id IS NULL
        """
    ))


def downgrade() -> None:
    # Best-effort: do not attempt to revert specific backfilled values
    # Leaving as a no-op to avoid data loss; manual revert can be performed if needed
    pass

