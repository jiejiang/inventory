"""empty message

Revision ID: 486a4b255e0e
Revises: 65b0c6d89f7a
Create Date: 2017-02-12 14:08:46.591759

"""

# revision identifiers, used by Alembic.
revision = '486a4b255e0e'
down_revision = '65b0c6d89f7a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('job', sa.Column('issuer', sa.String(length=128), nullable=True))
    op.create_index(op.f('ix_job_issuer'), 'job', ['issuer'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_job_issuer'), table_name='job')
    op.drop_column('job', 'issuer')
    ### end Alembic commands ###