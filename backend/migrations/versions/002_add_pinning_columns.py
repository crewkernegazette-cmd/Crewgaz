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
    # Check if columns exist before adding
    conn = op.get_bind()
    
    # Check for pinned_at column
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'articles' AND column_name = 'pinned_at'
    """))
    
    if not result.fetchone():
        op.add_column('articles', sa.Column('pinned_at', sa.DateTime(timezone=True), nullable=True))
        op.create_index('ix_articles_pinned_at', 'articles', ['pinned_at'])
    
    # Check for priority column
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'articles' AND column_name = 'priority'
    """))
    
    if not result.fetchone():
        op.add_column('articles', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))
        op.create_index('ix_articles_priority', 'articles', ['priority'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_articles_priority', table_name='articles')
    op.drop_index('ix_articles_pinned_at', table_name='articles')
    
    # Remove columns
    op.drop_column('articles', 'priority')
    op.drop_column('articles', 'pinned_at')