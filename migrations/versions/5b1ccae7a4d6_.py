"""empty message

Revision ID: 5b1ccae7a4d6
Revises: a4221c978242
Create Date: 2018-08-22 21:27:19.423458

"""

# revision identifiers, used by Alembic.
revision = '5b1ccae7a4d6'
down_revision = 'a4221c978242'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('route', sa.Column('code', sa.String(length=128), nullable=False))
    op.create_index(op.f('ix_route_code'), 'route', ['code'], unique=True)
    op.drop_index('ix_route_name', table_name='route')
    op.drop_column('route', 'display_name')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('route', sa.Column('display_name', sa.VARCHAR(length=128), autoincrement=False, nullable=False))
    op.create_index('ix_route_name', 'route', ['name'], unique=True)
    op.drop_index(op.f('ix_route_code'), table_name='route')
    op.drop_column('route', 'code')
    ### end Alembic commands ###