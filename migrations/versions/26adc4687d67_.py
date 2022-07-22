"""empty message

Revision ID: 26adc4687d67
Revises: 567964af9dbb
Create Date: 2021-03-23 11:04:55.964158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26adc4687d67'
down_revision = '567964af9dbb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('features', sa.Column(
        'gene_encode_id', sa.String(), nullable=True))
    op.add_column('features', sa.Column(
        'gene_symbol', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('features', 'gene_symbol')
    op.drop_column('features', 'gene_encode_id')
    # ### end Alembic commands ###
