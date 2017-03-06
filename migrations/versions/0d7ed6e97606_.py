"""empty message

Revision ID: 0d7ed6e97606
Revises: aa922fbc22b7
Create Date: 2016-11-20 01:26:17.482146

"""

# revision identifiers, used by Alembic.
revision = '0d7ed6e97606'
down_revision = 'aa922fbc22b7'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_info', sa.Column('billing_unit', sa.String(length=32), nullable=True))
    op.add_column('product_info', sa.Column('billing_unit_code', sa.String(length=32), nullable=True))
    op.add_column('product_info', sa.Column('gross_weight', sa.Float(), nullable=True))
    op.add_column('product_info', sa.Column('tax_code', sa.String(length=64), nullable=True))
    op.add_column('product_info', sa.Column('unit_per_item', sa.Float(), nullable=True))
    op.add_column('product_info', sa.Column('unit_price', sa.Float(), nullable=True))
    op.alter_column('product_info', 'price_per_kg',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('product_info', 'price_per_kg',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.drop_column('product_info', 'unit_price')
    op.drop_column('product_info', 'unit_per_item')
    op.drop_column('product_info', 'tax_code')
    op.drop_column('product_info', 'gross_weight')
    op.drop_column('product_info', 'billing_unit_code')
    op.drop_column('product_info', 'billing_unit')
    ### end Alembic commands ###