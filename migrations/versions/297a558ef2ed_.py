"""empty message

Revision ID: 297a558ef2ed
Revises: 6607082abe8e
Create Date: 2019-05-09 15:14:34.474334

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '297a558ef2ed'
down_revision = '6607082abe8e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('operations_statuses_idx', 'operations_statuses', ['operation_id', 'status'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('operations_statuses_idx', 'operations_statuses', type_='unique')
    # ### end Alembic commands ###
