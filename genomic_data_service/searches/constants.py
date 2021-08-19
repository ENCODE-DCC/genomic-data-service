OPTIONAL_PARAMS = [
    'annotation',
    'cart',
    'datastore',
    'debug',
    'field',
    'filterresponse',
    'format',
    'frame',
    'from',
    'genome',
    'limit',
    'mode',
    'referrer',
    'region',
    'remove',
    'sort',
    'type',
    'config',
]


FREE_TEXT_QUERIES = [
    'advancedQuery',
    'searchTerm',
]


RESERVED_KEYS = NOT_FILTERS = OPTIONAL_PARAMS + FREE_TEXT_QUERIES


DEFAULT_RNA_EXPRESSION_SORT = [
    '-expression.tpm',
    'gene.symbol',
]
