"""empty message

Revision ID: 96c80c4a3950
Revises: d9a13bbbf6c5
Create Date: 2018-04-25 21:28:59.538120

"""

# revision identifiers, used by Alembic.
revision = '96c80c4a3950'
down_revision = 'd9a13bbbf6c5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_info', sa.Column('ticket_name', sa.String(length=128), nullable=True))
    op.add_column('product_info', sa.Column('ticket_price', sa.Float(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_info', 'ticket_price')
    op.drop_column('product_info', 'ticket_name')
    ### end Alembic commands ###
