"""empty message

Revision ID: 8a3679db4c14
Revises: 538b45d48161
Create Date: 2016-07-07 14:49:23.841179

"""

# revision identifiers, used by Alembic.
revision = '8a3679db4c14'
down_revision = '538b45d48161'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('retraction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=64), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_retraction_uuid'), 'retraction', ['uuid'], unique=True)
    op.add_column(u'order', sa.Column('retraction_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'order', 'retraction', ['retraction_id'], ['id'])
    op.drop_column(u'order', 'retracted')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'order', sa.Column('retracted', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'order', type_='foreignkey')
    op.drop_column(u'order', 'retraction_id')
    op.drop_index(op.f('ix_retraction_uuid'), table_name='retraction')
    op.drop_table('retraction')
    ### end Alembic commands ###