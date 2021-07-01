AT_ID = '@id'

AT_TYPE = '@type'

BASE_PATH = '/tmp/'

DATASET = 'dataset'

DATASETS = 'datasets'

DATASET_FIELDS = [
    '@id',
    'biosample_summary',
    'replicates',
]

DOMAIN = 'https://www.encodeproject.org'

DOCUMENT_PREFIX = 'embedded'

ENSEMBL_PREFIX = 'ENSEMBL:'

EXPRESSION_AT_TYPE = ['RNAExpression', 'Item']

EXPRESSION_ID = 'expression_id'

FILE = 'file'

FILES = 'files'

FILE_FIELDS = [
     '@id',
    'assay_title',
    'assembly',
    'biosample_ontology',
    'dataset',
    'donors',
    'genome_annotation',
]

GENES = 'genes'

GENE_FIELDS = [
    '@id',
    'geneid',
    'name',
    'symbol',
    'synonyms',
    'title',
]

EXPRESSION_INDEX = 'rna-expression'

EXPRESSION_DOC_TYPE = 'rna-expression'

INDEXING_FIELDS = {
    '_index': EXPRESSION_INDEX,
    '_type': EXPRESSION_DOC_TYPE,
    'principals_allowed.view': ["system.Everyone"]
}
