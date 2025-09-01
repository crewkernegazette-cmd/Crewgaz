"""Add slug field to articles table

Revision ID: 001_add_slug_to_articles
Revises: 
Create Date: 2025-01-31 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_slug_to_articles'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add slug column to articles table"""
    # Check if column exists before adding
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'articles' AND column_name = 'slug'
    """))
    
    if not result.fetchone():
        # Add slug column
        op.add_column('articles', sa.Column('slug', sa.String(length=255), nullable=True))
        
        # Create unique index on slug
        op.create_index('ix_articles_slug', 'articles', ['slug'], unique=True)
    
    # Backfill slugs for existing articles
    # This will be handled in the application code using generate_slug function


def downgrade() -> None:
    """Remove slug column from articles table"""
    # Drop index first
    op.drop_index('ix_articles_slug', table_name='articles')
    
    # Drop column
    op.drop_column('articles', 'slug')