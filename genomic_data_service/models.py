from genomic_data_service import app, db

class Feature(db.Model):
    __tablename__ = 'features'

    gene_id = db.Column(db.String(), primary_key=True)
    transcript_id = db.Column(db.String(), primary_key=True)

    gene_name = db.Column(db.String(), nullable=False)
    transcript_name = db.Column(db.String(), nullable=False)


class Expression(db.Model):
    __tablename__ = 'expressions'

    transcript_id = db.Column(db.String(), primary_key=True)
    dataset_accession = db.Column(db.String(), primary_key=True)
    file_id = db.Column(db.String(), db.ForeignKey('files.id'), primary_key=True)

    tpm = db.Column(db.String())
    fpkm = db.Column(db.String())
    version = db.Column(db.String())
    assembly = db.Column(db.String())

    file = db.relationship('File',
        backref=db.backref('expressions', lazy=True))


file_tags = db.Table('file_tags',
    db.Column('file_id', db.String(), db.ForeignKey('files.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True))


class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.String(), primary_key=True)

    file_type = db.Column(db.String(), nullable=False)
    url = db.Column(db.String(), nullable=False)
    version = db.Column(db.String(), nullable=False)

    study_id = db.Column(db.String(), db.ForeignKey('studies.id'),
        nullable=False)
    study = db.relationship('Study',
        backref=db.backref('files', lazy=True))

    tags = db.relationship('Tag', secondary=file_tags, lazy='subquery',
        backref=db.backref('files', lazy=True))


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


study_tags = db.Table('study_tags',
    db.Column('study_id', db.String(), db.ForeignKey('studies.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True))


class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column(db.String(), primary_key=True)

    version = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    parent_project_id = db.Column(db.String(), nullable=False)
    tags = db.relationship('Tag', secondary=study_tags, lazy='subquery',
        backref=db.backref('studies', lazy=True))


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)

    
