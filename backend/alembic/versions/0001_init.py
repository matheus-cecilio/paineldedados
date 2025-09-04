"""create initial tables

Revision ID: 0001_init
Revises: 
Create Date: 2025-09-04 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

    op.create_table(
        'customers',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=True, unique=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
    )

    op.create_table(
        'categories',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('parent_id', pg.UUID(as_uuid=True), nullable=True),
    )

    op.create_table(
        'products',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('sku', sa.Text(), nullable=False, unique=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('category_id', pg.UUID(as_uuid=True), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('price', sa.Numeric(), nullable=False, server_default='0'),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
    )

    op.create_table(
        'sales',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', pg.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('customer_id', pg.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('qty', sa.Integer(), nullable=False),
        sa.Column('price_unit', sa.Numeric(), nullable=False),
        sa.Column('total', sa.Numeric(), nullable=False),
        sa.Column('sale_date', sa.TIMESTAMP(), nullable=False),
        sa.Column('source', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
    )

    op.create_table(
        'imports',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.Column('uploaded_by', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('finished_at', sa.TIMESTAMP(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('imports')
    op.drop_table('sales')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('customers')
