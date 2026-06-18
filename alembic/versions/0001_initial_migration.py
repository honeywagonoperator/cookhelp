"""Initial migration: create recipes table with pgvector

Revision ID: 0001
Revises:
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, VECTOR
import uuid

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'recipes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(500), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('ingredients', JSONB, nullable=False, default=list),
        sa.Column('steps', JSONB, nullable=False, default=list),
        sa.Column('tags', JSONB, nullable=False, default=list),
        sa.Column('source', JSONB, nullable=False, default=dict),
        sa.Column('embedding', VECTOR(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.execute('''
        CREATE INDEX IF NOT EXISTS idx_recipes_embedding_hnsw
        ON recipes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')


def downgrade() -> None:
    op.drop_index('idx_recipes_embedding_hnsw', table_name='recipes')
    op.drop_table('recipes')
    op.execute('DROP EXTENSION IF EXISTS vector')