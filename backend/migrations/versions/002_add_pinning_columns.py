"""Add pinning columns to articles

Revision ID: 002_add_pinning_columns
Revises: 001_add_slug_to_articles
Create Date: 2025-08-31 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_pinning_columns'
down_revision = '001_add_slug_to_articles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pinning columns to articles table
    op.add_column('articles', sa.Column('pinned_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('articles', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))
    
    # Create indexes for better query performance
    op.create_index('ix_articles_pinned_at', 'articles', ['pinned_at'])
    op.create_index('ix_articles_priority', 'articles', ['priority'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_articles_priority', table_name='articles')
    op.drop_index('ix_articles_pinned_at', table_name='articles')
    
    # Remove columns
    op.drop_column('articles', 'priority')
    op.drop_column('articles', 'pinned_at')