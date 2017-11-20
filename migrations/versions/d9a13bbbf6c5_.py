"""empty message

Revision ID: d9a13bbbf6c5
Revises: 42c70a9f733b
Create Date: 2017-11-14 14:10:40.271006

"""

# revision identifiers, used by Alembic.
revision = 'd9a13bbbf6c5'
down_revision = '42c70a9f733b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_info', sa.Column('report_name', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_info', 'report_name')
    ### end Alembic commands ###