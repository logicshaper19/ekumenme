"""
Add organization_id to conversations for multi-tenant scoping

Revision ID: add_conversation_organization_id
Revises: fix_bbch_universal_schema
Create Date: 2025-10-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_conversation_organization_id'
down_revision = 'fix_bbch_universal_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column as nullable first to avoid failing on existing rows
    op.add_column('conversations', sa.Column('organization_id', sa.UUID(), nullable=True))
    # Create index for faster lookups
    op.create_index('ix_conversations_organization_id', 'conversations', ['organization_id'], unique=False)
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_conversations_organization',
        source_table='conversations',
        referent_table='organizations',
        local_cols=['organization_id'],
        remote_cols=['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key, index, and column
    op.drop_constraint('fk_conversations_organization', 'conversations', type_='foreignkey')
    op.drop_index('ix_conversations_organization_id', table_name='conversations')
    op.drop_column('conversations', 'organization_id')

