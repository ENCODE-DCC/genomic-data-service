from genomic_data_service import app, db
import csv
import hashlib

class Feature(db.Model):
    __tablename__ = 'features'

    gene_id = db.Column(db.String(), primary_key=True)
    transcript_id = db.Column(db.String(), primary_key=True)

    gene_name = db.Column(db.String(), nullable=True)
    transcript_name = db.Column(db.String(), nullable=True)


class Expression(db.Model):
    __tablename__ = 'expressions'

    id = db.Column(db.String(), primary_key=True)
    transcript_id = db.Column(db.String())
    dataset_accession = db.Column(db.String())
    file_id = db.Column(db.String(), db.ForeignKey('files.id'))

    tpm = db.Column(db.String())
    fpkm = db.Column(db.String())
    version = db.Column(db.String())
    assembly = db.Column(db.String())
    assembly_version = db.Column(db.String())

    FILTERS = []
    TSV_HEADERS = ['geneID', 'tpm']

    file = db.relationship('File',
        backref=db.backref('expressions', lazy=True))

    def to_tsv_row(self):
        return [self.transcript_id, self.tpm]
    

file_tags = db.Table('file_tags',
    db.Column('file_id', db.String(), db.ForeignKey('files.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True))


class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.String(), primary_key=True)

    file_type = db.Column(db.String(), nullable=False)
    url = db.Column(db.String(), nullable=False)
    version = db.Column(db.String(), nullable=False)
    md5 = db.Column(db.String(), nullable=False)

    study_id = db.Column(db.String(), db.ForeignKey('studies.id'),
                         nullable=False)
    study = db.relationship('Study',
        backref=db.backref('files', lazy=True))

    tags = db.relationship('Tag', secondary=file_tags, lazy='subquery',
        backref=db.backref('files', lazy=True))

    # defaulting to TPM, follow up on: https://github.com/ga4gh-rnaseq/schema/issues/93
    DEFAULT_UNITS = 'TPM'
    
    def to_dict(self):
        return {
            'fileType': self.file_type,
            'version': self.version,
            'id': self.id,
            'units': self.DEFAULT_UNITS, 
            'studyID': self.study_id,
            'url': self.url,
            'md5': self.md5
        }

    def generate_file_from_feature_list(self, feature_names, feature_ids, path, request_host):
        content = self.expressions_with_feature_list(feature_names, feature_ids)

        key_string = ",".join(sorted(feature_names or []) + (feature_ids or []))
        key = hashlib.sha224(key_string.encode()).hexdigest()

        file_name = self.id + "_" + key + "." + self.file_type
        file_path = path + file_name

        with open(file_path, 'w', newline='') as file_output:
            tsv_output = csv.writer(file_output, delimiter='\t')
            for row in content:
                tsv_output.writerow(row)

        md5 = hashlib.md5(open(file_path,'rb').read()).hexdigest()

        return {
            'fileType': self.file_type,
            'version': self.version,
            'id': key,
            'units': self.DEFAULT_UNITS,
            'studyID': self.study_id,
            'url': request_host + '/download/' + file_name,
            'md5': md5
        }

    def expressions_with_feature_list(self, gene_names, gene_ids):
        transcript_ids = Feature.query.with_entities(Feature.transcript_id)

        if gene_names:
            transcript_ids = transcript_ids.filter(Feature.gene_name.in_(gene_names))
        if gene_ids:
            transcript_ids = transcript_ids.filter(Feature.gene_id.in_(gene_ids))

        transcript_ids = transcript_ids.all()

        expressions = Expression.query.filter_by(file_id=self.id).filter(Expression.transcript_id.in_(transcript_ids)).all()
        return ([Expression.TSV_HEADERS] + [expression.to_tsv_row() for expression in expressions])


project_tags = db.Table('project_tags',
    db.Column('project_id', db.String(), db.ForeignKey('projects.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True))


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.String(), primary_key=True)

    version = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    tags = db.relationship('Tag', secondary=project_tags, lazy='subquery',
        backref=db.backref('projects', lazy=True))

    FILTERS = []
    
    def to_dict(self):
        return {
            'version': self.version,
            'description': self.description,
            'id': self.id,
            'name': self.name
        }


study_tags = db.Table('study_tags',
    db.Column('study_id', db.String(), db.ForeignKey('studies.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True))


class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column(db.String(), primary_key=True)

    version = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    genome = db.Column(db.String(), nullable=True)

    parent_project_id = db.Column(db.String(), db.ForeignKey('projects.id'),
        nullable=False)
    parent_project = db.relationship('Project',
        backref=db.backref('studies', lazy=True))

    tags = db.relationship('Tag', secondary=study_tags, lazy='subquery',
        backref=db.backref('studies', lazy=True))

    FILTERS = []
    
    def to_dict(self):
        return {
            'version': self.version,
            'id': self.id,
            'description': self.description,
            'parentProjectID': self.parent_project_id,
            'name': self.name,
            'genome': self.genome
        }


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }
