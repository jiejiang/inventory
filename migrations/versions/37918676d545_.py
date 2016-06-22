"""empty message

Revision ID: 37918676d545
Revises: f345cca3f384
Create Date: 2016-06-22 11:14:47.762952

"""

# revision identifiers, used by Alembic.
revision = '37918676d545'
down_revision = 'f345cca3f384'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('city',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['city.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('city')
    ### end Alembic commands ###
