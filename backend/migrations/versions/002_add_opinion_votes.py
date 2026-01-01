"""Add upvotes and downvotes columns to trending_opinions

Revision ID: 002_add_opinion_votes
Revises: 001_add_slug_to_articles
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_add_opinion_votes'
down_revision = '001_add_slug_to_articles'
branch_labels = None
depends_on = None

def upgrade():
    # Add upvotes column if it doesn't exist
    try:
        op.add_column('trending_opinions', sa.Column('upvotes', sa.Integer(), nullable=True, server_default='0'))
    except Exception as e:
        print(f"Column 'upvotes' may already exist: {e}")
    
    # Add downvotes column if it doesn't exist
    try:
        op.add_column('trending_opinions', sa.Column('downvotes', sa.Integer(), nullable=True, server_default='0'))
    except Exception as e:
        print(f"Column 'downvotes' may already exist: {e}")

def downgrade():
    try:
        op.drop_column('trending_opinions', 'upvotes')
    except Exception:
        pass
    try:
        op.drop_column('trending_opinions', 'downvotes')
    except Exception:
        pass
