"""add_missing_user_profile_columns

Revision ID: 08fbde581c72
Revises: ensure_user_columns_exist
Create Date: 2025-10-02 21:05:27.942713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08fbde581c72'
down_revision: Union[str, Sequence[str], None] = 'ensure_user_columns_exist'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing profile columns
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS profile_picture_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS bio TEXT,
        ADD COLUMN IF NOT EXISTS experience_years VARCHAR(10),
        ADD COLUMN IF NOT EXISTS specialization VARCHAR[],
        ADD COLUMN IF NOT EXISTS region_code VARCHAR(20),
        ADD COLUMN IF NOT EXISTS department_code VARCHAR(10),
        ADD COLUMN IF NOT EXISTS commune_insee VARCHAR(10),
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
        ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP WITH TIME ZONE
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove added columns
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS profile_picture_url,
        DROP COLUMN IF EXISTS bio,
        DROP COLUMN IF EXISTS experience_years,
        DROP COLUMN IF EXISTS specialization,
        DROP COLUMN IF EXISTS region_code,
        DROP COLUMN IF EXISTS department_code,
        DROP COLUMN IF EXISTS commune_insee,
        DROP COLUMN IF EXISTS is_active,
        DROP COLUMN IF EXISTS is_verified,
        DROP COLUMN IF EXISTS is_superuser,
        DROP COLUMN IF EXISTS email_verified_at
    """)
