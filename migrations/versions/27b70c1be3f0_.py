"""empty message

Revision ID: 27b70c1be3f0
Revises: e7cf6ce136f4
Create Date: 2021-04-01 10:18:11.615734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27b70c1be3f0'
down_revision = 'e7cf6ce136f4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('files', sa.Column('biosample_classification', sa.String(), nullable=True))
    op.add_column('files', sa.Column('biosample_organ', sa.String(), nullable=True))
    op.add_column('files', sa.Column('biosample_summary', sa.String(), nullable=True))
    op.add_column('files', sa.Column('biosample_system', sa.String(), nullable=True))
    op.add_column('files', sa.Column('biosample_term_name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('files', 'biosample_term_name')
    op.drop_column('files', 'biosample_system')
    op.drop_column('files', 'biosample_summary')
    op.drop_column('files', 'biosample_organ')
    op.drop_column('files', 'biosample_classification')
    # ### end Alembic commands ###
