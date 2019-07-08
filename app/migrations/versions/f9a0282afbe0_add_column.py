"""add column

Revision ID: f9a0282afbe0
Revises: 
Create Date: 2018-03-30 11:15:36.769457

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f9a0282afbe0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('script_task', sa.Column('asset_num', mysql.INTEGER, nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('script_task', 'asset_num')
    # ### end Alembic commands ###
