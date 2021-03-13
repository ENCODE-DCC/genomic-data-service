import hashlib
import csv
from genomic_data_service.models import File, Feature, Expression
from sqlalchemy import func, cast, DECIMAL

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
        self.page = int(params.get('page') or 1)
        self.sort_by = params.get('sort')

        if params.get('units') in Expression.AVAILABLE_UNITS:
            self.units = params.get('units')
        else:
            self.units = Expression.DEFAULT_UNITS

        if self.gene_ids:
            self.gene_ids = self.gene_ids.split(",")

        if self.gene_names:
            self.resolve_gene_ids(self.gene_names.split(","))

        if self.sample_ids:
            self.sample_ids = self.sample_ids.split(",")

        if self.file_id:
            self.file_ids = [self.file_id]
        else:
            self.fetch_file_ids()

        self.should_calculate_facets = self.file_type == 'json'

        self.transcript_ids = []
            
        self.fetch_expressions()


    def resolve_gene_ids(self, gene_names):
        features = Feature.query.with_entities(Feature.gene_id).filter(Feature.gene_name.in_(self.gene_names)).all()

        self.gene_ids += [feature.gene_id for feature in features]


    def get_expressions(self):
        headers = self.get_tsv_headers()

        if self.file_type == 'tsv':
            return ([headers] + self.expressions)
        elif self.file_type == 'json':
            expressions = []

            for expression in self.expressions:
                expression_dict = {}
                for i, header in enumerate(headers):
                    expression_dict[header] = expression[i]
                expressions.append(expression_dict)

            return expressions
        else:
            return self.expressions


    def get_tsv_headers(self):
        return Expression.TSV_HEADERS + [self.units] + File.TSV_HEADERS


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
            ticket['studyID'] = self.study_id

        return ticket


    def valid_expression_id(self):
        return (self.file_id and (File.query.filter_by(id=self.file_id).count() == 1))


    def unacceptable_format(self):
        return (not self.file_type or (self.file_type not in File.ACCEPTED_FORMATS))


    def fetch_file_ids(self):
        self.file_ids= []

        files = File.query.with_entities(File.id)
        empty_query = str(files)

        if self.project_id:
            files = files.filter_by(project_id=self.project_id)

        if self.study_id:
            files = files.filter_by(study_id=self.study_id)

        if self.sample_ids:
            files = files.filter(File.study_id.in_(self.sample_ids))

        if self.version:
            files = files.filter_by(version=self.version)

        if str(files) != empty_query:
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
        expression_attributes = [getattr(Expression, attr) for attr in Expression.TSV_ATTRIBUTES + [self.units]]
        file_attributes = [getattr(File, attr) for attr in File.TSV_ATTRIBUTES]
        attributes = expression_attributes + file_attributes

        expressions = Expression.query.join(File).with_entities(*attributes)

        if len(self.transcript_ids) > 0:
            expressions = expressions.filter(Expression.feature_id.in_(self.transcript_ids))
        elif (self.gene_ids and len(self.gene_ids) > 0):
            expressions = expressions.filter(Expression.feature_id.in_(self.gene_ids))

        if len(self.file_ids) > 0:
            expressions = expressions.filter(Expression.file_id.in_(self.file_ids))

        self.total = expressions.count()

        if self.should_calculate_facets:
            self.calculate_facets(expressions)

        if self.sort_by:
            sort_by = self.sort_by

            desc = False
            if self.sort_by[0] == '-':
                desc = True
                sort_by = sort_by[1:]

            for model in [Expression, File]:
                if sort_by in model.TSV_MAP.keys():
                    field = getattr(model, model.TSV_MAP[sort_by])

                    if sort_by in ['tpm', 'fpkm']:
                        field = cast(field, DECIMAL)

                    if desc:
                        field = field.desc()

                    expressions = expressions.order_by(field)
                    break

        if self.page:
            self.expressions = expressions.paginate(self.page, Expression.PER_PAGE, False).items
        else:
            self.expressions = expressions.all()

        self.format_metadata()


    def calculate_facets(self, expressions):
        assays = expressions.with_entities(File.assay, func.count(File.assay)).group_by(File.assay).all()

        self.facets = {
            'assayType': expressions.with_entities(File.assay, func.count(File.assay)).group_by(File.assay).all(),
            'annotation': expressions.with_entities(File.assembly, func.count(File.assembly)).group_by(File.assembly).all()
        }

        for key in self.facets:
            self.facets[key] = [[facet[0], facet[1]] for facet in self.facets[key]]


    def format_metadata(self):
        metadata_expressions = []

        metadata_dictionary = {**Expression.TSV_MAP, **File.TSV_MAP}
        metadata_headers = self.get_tsv_headers()

        for expression in self.expressions:
            exp = []

            for header in metadata_headers:
                component = metadata_dictionary[header]

                if isinstance(component, list):
                    value = getattr(expression, component[1])
                    exp.append(component[0].format(value))
                else:
                    exp.append(getattr(expression, component))

            metadata_expressions.append(exp)

        self.expressions = metadata_expressions
