"""Update embedding dimension from 1024 to 2048

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-18
"""
from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_recipes_embedding_hnsw')
    op.execute('DROP INDEX IF EXISTS idx_recipes_embedding_ivfflat')
    op.drop_column('recipes', 'embedding')
    op.add_column('recipes', sa.Column('embedding', Vector(2048), nullable=True))


def downgrade() -> None:
    op.drop_column('recipes', 'embedding')
    op.add_column('recipes', sa.Column('embedding', Vector(1024), nullable=True))

    op.execute('''
        CREATE INDEX IF NOT EXISTS idx_recipes_embedding_hnsw
        ON recipes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')
