"""Add category_labels column to articles

Revision ID: 003_add_category_labels
Revises: 002_add_pinning_columns
Create Date: 2025-09-01 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_category_labels'
down_revision = '002_add_pinning_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add category_labels column to articles table
    op.add_column('articles', sa.Column('category_labels', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove category_labels column
    op.drop_column('articles', 'category_labels')