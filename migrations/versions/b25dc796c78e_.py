"""empty message

Revision ID: b25dc796c78e
Revises: 5b1ccae7a4d6
Create Date: 2018-11-01 10:59:27.194155

"""

# revision identifiers, used by Alembic.
revision = 'b25dc796c78e'
down_revision = '5b1ccae7a4d6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('retraction', sa.Column('is_redo', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('retraction', 'is_redo')
    ### end Alembic commands ###
