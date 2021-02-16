from genomic_data_service import db
import csv
import datetime
import requests
import redis
import uuid

import os.path
from os import path


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

    @staticmethod
    def prefix_id(id):
        try:
            int(id)
            return 'tRNAscan:' + str(id)
        except ValueError:
            return id


class Expression(db.Model):
    __tablename__ = 'expressions'

    id = db.Column(db.String(), primary_key=True)
    feature_id = db.Column(db.String(), nullable=False, index=True)
    feature_type = db.Column(db.String(), nullable=False)
    dataset_accession = db.Column(db.String())
    file_id = db.Column(db.String(), db.ForeignKey('files.id'), index=True)

    tpm = db.Column(db.String())
    fpkm = db.Column(db.String())

    FILTERS = []
    TSV_HEADERS = ['featureID', 'tpm', 'expressionID']

    # tsv column name => object key
    TSV_MAP = {
        'featureID': 'feature_id',
        'tpm': 'tpm',
        'expressionID': 'file_id'
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
    REJECT_LIST_ASSAYS_INGESTION = ['CAGE', 'RAMPAGE']

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
        filedir = "/tmp/" # TODO: make it configurable
        filename = self.id + "." + self.file_type

        if path.exists(filedir + filename):
            disk_file = open(filedir + filename, 'r')

            if self.file_type == 'tsv':
                return csv.reader(disk_file, delimiter="\t", quotechar='"')

        print("Downloading " + self.url)

        file = requests.get(self.url)

        if file.status_code != 200:
            print("Failed to download file " + self.url)
            return None

        with open(filedir + filename, 'wb') as disk_file:
            disk_file.write(file.content)

        if self.file_type == 'tsv':
            expression_data = file.content.decode("utf-8").splitlines()
            return(csv.reader(expression_data , delimiter="\t", quotechar='"'))

        return None


    def existing_feature_ids(self):
        existing_expressions = Expression.query.with_entities(Expression.feature_id).filter(Expression.dataset_accession == self.study_id).all()

        return [expression[0] for expression in existing_expressions]


    def import_expressions(self):
        if self.file_indexed_at:
            print("Expressions already indexed.")
            return

        if self.assay in File.REJECT_LIST_ASSAYS_INGESTION:
            print("Assay currently not supported.")
            return

        parsed_file = self.fetch_and_parse()

        if not parsed_file:
            return

        header = next(parsed_file)

        try:
            fields = {
                'gene_id': header.index('gene_id'),
                'transcript_ids': header.index('transcript_id(s)'),
                'tpm': header.index('TPM'),
                'fpkm': header.index('FPKM')
            }
        except ValueError:
            raise ValueError("File " + self.study_id + " has an invalid format")

        cache = redis.Redis()

        expressions = []

        existing_feature_ids = self.existing_feature_ids()

        for row in parsed_file:
            gene_id = Feature.prefix_id(row[fields['gene_id']])

            if gene_id in existing_feature_ids:
                continue
            
            transcript_ids = row[fields['transcript_ids']].split(',')

            expressions.append(
                Expression(
                    id=uuid.uuid4(),
                    feature_id=gene_id,
                    feature_type='gene_id',
                    dataset_accession=self.study_id,
                    tpm=row[fields['tpm']],
                    fpkm=row[fields['fpkm']],
                    file_id=self.id
                )
            )

            for transcript_id in transcript_ids:
                cache.sadd(gene_id, transcript_id)

        for expression in expressions:
            db.session.add(expression)

        self.file_indexed_at = str(datetime.datetime.now())
        db.session.add(self)

        db.session.commit()
