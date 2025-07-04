"""Add image_path to Product model

Revision ID: f84fbb594fb4
Revises: 5eb21ea5e3d3
Create Date: 2025-06-24 12:17:41.438089

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f84fbb594fb4'
down_revision = '5eb21ea5e3d3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_path', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_column('image_path')

    # ### end Alembic commands ###
