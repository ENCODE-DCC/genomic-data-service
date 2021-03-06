"""empty message

Revision ID: e7cf6ce136f4
Revises: 26adc4687d67
Create Date: 2021-03-25 08:27:05.660927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7cf6ce136f4'
down_revision = '26adc4687d67'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('genes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('encode_id', sa.String(), nullable=True),
    sa.Column('symbol', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('features', 'transcript_name')
    op.drop_column('features', 'gene_encode_id')
    op.drop_column('features', 'gene_name')
    op.drop_column('features', 'gene_symbol')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('features', sa.Column('gene_symbol', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('features', sa.Column('gene_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('features', sa.Column('gene_encode_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('features', sa.Column('transcript_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_table('genes')
    # ### end Alembic commands ###
