"""empty message

Revision ID: 567964af9dbb
Revises: 1c19d9abe7d9
Create Date: 2021-03-10 13:33:12.602289

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '567964af9dbb'
down_revision = '1c19d9abe7d9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('files', sa.Column('analysis_id', sa.String(), nullable=True))
    op.add_column('files', sa.Column('biosample_sex', sa.String(), nullable=True))
    op.add_column('files', sa.Column('cell_line_id', sa.String(), nullable=True))
    op.add_column('files', sa.Column('cell_line_label', sa.String(), nullable=True))
    op.add_column('files', sa.Column('cell_type_id', sa.String(), nullable=True))
    op.add_column('files', sa.Column('cell_type_label', sa.String(), nullable=True))
    op.add_column('files', sa.Column('disease_term_id', sa.String(), nullable=True))
    op.add_column('files', sa.Column('organism_id', sa.String(), nullable=True))
    op.add_column('files', sa.Column('organism_scientific_name', sa.String(), nullable=True))
    op.add_column('files', sa.Column('tissue_id', sa.String(), nullable=True))
    op.add_column('files', sa.Column('tissue_label', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('files', 'tissue_label')
    op.drop_column('files', 'tissue_id')
    op.drop_column('files', 'organism_scientific_name')
    op.drop_column('files', 'organism_id')
    op.drop_column('files', 'disease_term_id')
    op.drop_column('files', 'cell_type_label')
    op.drop_column('files', 'cell_type_id')
    op.drop_column('files', 'cell_line_label')
    op.drop_column('files', 'cell_line_id')
    op.drop_column('files', 'biosample_sex')
    op.drop_column('files', 'analysis_id')
    # ### end Alembic commands ###
