import hashlib
import csv
from genomic_data_service.models import File, Feature, Expression

class ExpressionService():
    def __init__(self, params):
        self.project_id = params.get('projectID')
        self.study_id = params.get('studyID')
        self.file_type = params.get('format', File.DEFAULT_FORMAT)
        self.version = params.get('version')
        self.gene_names = params.get('featureNameList')
        self.gene_ids = params.get('featureIDList')
        self.sample_ids = params.get('sampleIDList')
        self.file_id = params.get('expression_id')

        if self.gene_names:
            self.gene_names = self.gene_names.split(",")

        if self.gene_ids:
            self.gene_ids = self.gene_ids.split(",")

        if self.sample_ids:
            self.sample_ids = self.sample_ids.split(",")

        if self.file_id:
            self.file_ids = [self.file_id]
        else:
            self.fetch_file_ids()

        self.fetch_transcript_ids()
        self.fetch_expressions()


    def get_expressions(self):
        if self.file_type == 'tsv':
            return ([Expression.TSV_HEADERS] + self.expressions)
        else:
            return self.expressions


    def generate_filename(self, filename_prefix='Expressions'):
        new_file_id = ",".join(sorted(self.gene_names or []) + (self.gene_ids or []))
        new_file_signature = hashlib.sha224(new_file_id.encode()).hexdigest()

        return (filename_prefix + "_" + new_file_signature + "." + self.file_type)


    def store_expressions(self, server_file_path):
        with open(server_file_path, 'w', newline='') as file_output:
            tsv_output = csv.writer(file_output, delimiter='\t')
            for row in self.get_expressions():
                tsv_output.writerow(row)


    def get_file_ticket(self, server_storage_path, server_download_path):
        filename = self.generate_filename()
        server_file_path = server_storage_path + filename
        
        self.store_expressions(server_file_path)

        md5 = hashlib.md5(open(server_file_path,'rb').read()).hexdigest()

        ticket = {
            'units': File.DEFAULT_UNITS,
            'url': server_download_path + filename,
            'md5': md5,
            'headers': {},
            'fileType': self.file_type
        }

        if self.study_id:
            ticket['studyID'] = self.studyID

        return ticket


    def valid_expression_id(self):
        return (self.file_id and (File.query.filter_by(id=self.file_id).count() == 1))


    def unacceptable_format(self):
        return (not self.file_type or (self.file_type not in File.ACCEPTED_FORMATS))


    def fetch_file_ids(self):
        files = File.query.with_entities(File.id)

        if self.project_id:
            files = files.filter_by(project_id=self.project_id)
    
        if self.study_id:
            files = files.filter_by(study_id=self.study_id)

        if self.sample_ids:
            files = files.filter(File.study_id.in_(self.sample_ids))

        if self.version:
            files = files.filter_by(version=self.version)

        self.file_ids = files.all()


    def fetch_transcript_ids(self):
        if self.gene_names or self.gene_ids:
            transcript_ids = Feature.query.with_entities(Feature.transcript_id)

            if self.gene_names:
                transcript_ids = transcript_ids.filter(Feature.gene_name.in_(self.gene_names))

            if self.gene_ids:
                transcript_ids = transcript_ids.filter(Feature.gene_id.in_(self.gene_ids))

            self.transcript_ids = transcript_ids.all()
            return

        self.transcript_ids = []


    def fetch_expressions(self):
        if self.file_type == 'tsv':
            attributes = [getattr(Expression, attr) for attr in Expression.TSV_MAP.values()]
            expressions = Expression.query.with_entities(*attributes)
        else:
            expressions = Expression.query

        if len(self.transcript_ids) > 0:
            expressions = expressions.filter(Expression.transcript_id.in_(self.transcript_ids))

        if len(self.file_ids) > 0:
            expressions = expressions.filter(Expression.file_id.in_(self.file_ids))

        self.expressions = expressions.all()
