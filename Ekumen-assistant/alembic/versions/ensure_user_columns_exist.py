"""Ensure user preference columns exist

Revision ID: ensure_user_columns_exist
Revises: set_conversation_org_id_not_null
Create Date: 2025-10-02 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ensure_user_columns_exist'
down_revision = 'set_conversation_org_id_not_null'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to users table in a safe, idempotent way for dev
    # Note: use separate ALTER statements for broader Postgres compatibility
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) NOT NULL DEFAULT 'fr';
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) NOT NULL DEFAULT 'Europe/Paris';
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS notification_preferences TEXT;
        """
    )


def downgrade() -> None:
    # Non-destructive downgrade: keep columns (they may be used by code)
    # If needed, they can be manually dropped in a future controlled migration.
    pass

