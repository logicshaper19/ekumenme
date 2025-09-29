"""Add message threading support

Revision ID: add_message_threading
Revises: 
Create Date: 2025-09-29 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'add_message_threading'
down_revision = '9548328e3725'  # Latest revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add thread_id and parent_message_id columns to messages table"""
    
    # Add thread_id column for tracking message threads
    op.add_column('messages', sa.Column('thread_id', sa.String(100), nullable=True))
    op.create_index('ix_messages_thread_id', 'messages', ['thread_id'])
    
    # Add parent_message_id column for message replies
    op.add_column('messages', sa.Column('parent_message_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_messages_parent_message_id',
        'messages', 'messages',
        ['parent_message_id'], ['id']
    )


def downgrade() -> None:
    """Remove thread_id and parent_message_id columns from messages table"""
    
    # Remove foreign key constraint
    op.drop_constraint('fk_messages_parent_message_id', 'messages', type_='foreignkey')
    
    # Remove columns
    op.drop_index('ix_messages_thread_id', 'messages')
    op.drop_column('messages', 'thread_id')
    op.drop_column('messages', 'parent_message_id')
