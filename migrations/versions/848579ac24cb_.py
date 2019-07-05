"""empty message

Revision ID: 848579ac24cb
Revises: 96c80c4a3950
Create Date: 2018-05-23 16:38:22.538192

"""

# revision identifiers, used by Alembic.
revision = '848579ac24cb'
down_revision = '96c80c4a3950'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_info', sa.Column('waybill_name', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_info', 'waybill_name')
    ### end Alembic commands ###
