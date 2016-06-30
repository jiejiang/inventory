"""empty message

Revision ID: 3d8798dc99fa
Revises: 45dafd83a675
Create Date: 2016-06-29 21:54:46.289007

"""

# revision identifiers, used by Alembic.
revision = '3d8798dc99fa'
down_revision = '45dafd83a675'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('receiver_address', sa.String(length=256), nullable=True))
    op.add_column('order', sa.Column('receiver_id_number', sa.String(length=64), nullable=True))
    op.add_column('order', sa.Column('receiver_name', sa.String(length=32), nullable=True))
    op.add_column('order', sa.Column('sender_address', sa.String(length=256), nullable=True))
    op.drop_column('order', 'sender')
    op.drop_column('order', 'receiver')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('receiver', sa.VARCHAR(length=256), autoincrement=False, nullable=True))
    op.add_column('order', sa.Column('sender', sa.VARCHAR(length=256), autoincrement=False, nullable=True))
    op.drop_column('order', 'sender_address')
    op.drop_column('order', 'receiver_name')
    op.drop_column('order', 'receiver_id_number')
    op.drop_column('order', 'receiver_address')
    ### end Alembic commands ###