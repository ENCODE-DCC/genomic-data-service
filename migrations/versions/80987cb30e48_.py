"""empty message

Revision ID: 80987cb30e48
Revises:
Create Date: 2021-02-05 13:37:43.031725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80987cb30e48'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('features',
                    sa.Column('gene_id', sa.String(), nullable=False),
                    sa.Column('transcript_id', sa.String(), nullable=False),
                    sa.Column('gene_name', sa.String(), nullable=True),
                    sa.Column('transcript_name', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('gene_id', 'transcript_id')
                    )
    op.create_table('projects',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('version', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('studies',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('version', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('genome', sa.String(), nullable=True),
                    sa.Column('parent_project_id',
                              sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['parent_project_id'], ['projects.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('files',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('file_type', sa.String(), nullable=False),
                    sa.Column('url', sa.String(), nullable=False),
                    sa.Column('version', sa.String(), nullable=False),
                    sa.Column('md5', sa.String(), nullable=False),
                    sa.Column('assay', sa.String(), nullable=False),
                    sa.Column('assembly', sa.String(), nullable=False),
                    sa.Column('assembly_version', sa.String(), nullable=False),
                    sa.Column('file_indexed_at', sa.String(), nullable=True),
                    sa.Column('study_id', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('expressions',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('feature_id', sa.String(), nullable=False),
                    sa.Column('feature_type', sa.String(), nullable=False),
                    sa.Column('dataset_accession', sa.String(), nullable=True),
                    sa.Column('file_id', sa.String(), nullable=True),
                    sa.Column('tpm', sa.String(), nullable=True),
                    sa.Column('fpkm', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['file_id'], ['files.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('expressions')
    op.drop_table('files')
    op.drop_table('studies')
    op.drop_table('projects')
    op.drop_table('features')
    # ### end Alembic commands ###
