"""empty message

Revision ID: 848ba8913ce9
Revises: 983cb167deb8
Create Date: 2024-05-14 13:57:23.077905

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '848ba8913ce9'
down_revision = '983cb167deb8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('events') as batch_op:
        batch_op.add_column(sa.Column('eventype', sa.String(length=255), nullable=True, server_default='Default Event Type'))

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('events') as batch_op:
        batch_op.drop_column('eventype')

    # ### end Alembic commands ###
