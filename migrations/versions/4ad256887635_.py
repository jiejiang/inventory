"""empty message

Revision ID: 4ad256887635
Revises: 0d7ed6e97606
Create Date: 2017-01-19 12:08:16.761493

"""

# revision identifiers, used by Alembic.
revision = '4ad256887635'
down_revision = '0d7ed6e97606'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('job', sa.Column('version', sa.String(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('job', 'version')
    ### end Alembic commands ###
