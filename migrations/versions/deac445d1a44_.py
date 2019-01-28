"""empty message

Revision ID: deac445d1a44
Revises: b25dc796c78e
Create Date: 2018-12-05 20:05:20.290770

"""

# revision identifiers, used by Alembic.
revision = 'deac445d1a44'
down_revision = 'b25dc796c78e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_info', sa.Column('dutiable_as_any_4_pieces', sa.Boolean(), nullable=True))
    op.add_column('product_info', sa.Column('non_dutiable_as_all_6_pieces', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_info', 'non_dutiable_as_all_6_pieces')
    op.drop_column('product_info', 'dutiable_as_any_4_pieces')
    ### end Alembic commands ###