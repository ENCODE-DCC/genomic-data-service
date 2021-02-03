from genomic_data_service import db

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
    assembly = db.Column(db.String())
    assembly_version = db.Column(db.String())

    FILTERS = []
    TSV_HEADERS = ['featureID', 'tpm']

    # tsv column name => object key
    TSV_MAP = {
        'featureID': 'transcript_id',
        'tpm': 'tpm'
    }
    
    file = db.relationship('File',
        backref=db.backref('expressions', lazy=True))

    def to_tsv_row(self):
        return [self.transcript_id, self.tpm]
    

class File(db.Model):
    __tablename__ = 'files'

    DEFAULT_UNITS = 'TPM'
    DEFAULT_FORMAT = 'tsv'
    ACCEPTED_FORMATS = ['tsv']

    id = db.Column(db.String(), primary_key=True)

    file_type = db.Column(db.String(), nullable=False)
    url = db.Column(db.String(), nullable=False)
    version = db.Column(db.String(), nullable=False)
    md5 = db.Column(db.String(), nullable=False)

    study_id = db.Column(db.String(), db.ForeignKey('studies.id'),
                         nullable=False)
    study = db.relationship('Study',
        backref=db.backref('files', lazy=True))


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.String(), primary_key=True)

    version = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)

    FILTERS = []
    
    def to_dict(self):
        return {
            'version': self.version,
            'description': self.description,
            'id': self.id,
            'name': self.name
        }


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
