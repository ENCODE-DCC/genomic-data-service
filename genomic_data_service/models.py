from genomic_data_service import db
import csv
import datetime


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


class Feature(db.Model):
    __tablename__ = 'features'

    gene_id = db.Column(db.String(), primary_key=True)
    transcript_id = db.Column(db.String(), primary_key=True)

    gene_name = db.Column(db.String(), nullable=True)
    transcript_name = db.Column(db.String(), nullable=True)


class Expression(db.Model):
    __tablename__ = 'expressions'

    id = db.Column(db.String(), primary_key=True)
    feature_id = db.Column(db.String(), nullable=False)
    feature_type = db.Column(db.String(), nullable=False)
    dataset_accession = db.Column(db.String())
    file_id = db.Column(db.String(), db.ForeignKey('files.id'))

    tpm = db.Column(db.String())
    fpkm = db.Column(db.String())

    FILTERS = []
    TSV_HEADERS = ['featureID', 'tpm']

    # tsv column name => object key
    TSV_MAP = {
        'featureID': 'feature_id',
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
    assay = db.Column(db.String(), nullable=False)
    assembly = db.Column(db.String(), nullable=False)
    assembly_version = db.Column(db.String(), nullable=False)

    file_indexed_at = db.Column(db.String())

    study_id = db.Column(db.String(), db.ForeignKey('studies.id'),
                         nullable=False)
    study = db.relationship('Study',
        backref=db.backref('files', lazy=True))


    def fetch_and_parse(self):
        file = requests.get(self.url)

        if file.status_code != 200:
            print("Failed to download file " + self.url)
            return None

        if self.file_type == 'tsv':
            expression_data = file.content.decode("utf-8").splitlines()
            return(csv.reader(expression_data , delimiter="\t", quotechar='"'))

        return None


    def import_expressions(self):
        if file_indexed_at:
            return

        parsed_file = self.fetch_and_parse()

        if not parsed_file:
            return

        header = next(parsed_file)

        fields = {
            'gene_id': header.index('gene_id'),
            'transcript_ids': header.index('transcript_id(s)'),
            'tpm': header.index('TPM'),
            'fpkm': header.index('FPKM')
        }

        expressions = []
        features = []

        for row in parsed_file:
            gene_id = row[fields['gene_id']]
            transcript_ids = row[fields['transcript_ids']].split(',')

            expressions.append(
                Expression(
                    id=uuid.uuid4(),
                    feature_id=gene_id,
                    feature_type='gene_id',
                    dataset_accession=self.study_id,
                    tpm=row[fields['tpm']],
                    fpkm=row[fields['fpkm']],
                    file_id=self.id,
                    assembly=self.assembly,
                    assembly_version=self.assembly_version
                )
            )

            for transcript_id in transcript_ids:
                features.append(
                    Feature(
                        gene_id=gene_id,
                        transcript_id=transcript_id
                    )
                )

        for expression in expressions:
            db.session.add(expression)

        for feature in features:
            db.session.add(feature)

        self.file_indexed_at = str(datetime.datetime.now())
        db.session.add(self)

        db.session.commit()
