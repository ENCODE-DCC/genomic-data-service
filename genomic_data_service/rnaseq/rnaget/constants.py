PROJECTS = [
    {
        'id': 'ENCODE',
        'name': 'ENCODE: Encyclopedia of DNA Elements',
        'description': 'The Encyclopedia of DNA Elements (ENCODE) Consortium is an international collaboration of research groups funded by the National Human Genome Research Institute (NHGRI). The goal of ENCODE is to build a comprehensive parts list of functional elements in the human genome, including elements that act at the protein and RNA levels, and regulatory elements that control cells and circumstances in which a gene is active. ENCODE investigators employ a variety of assays and methods to identify functional elements. The discovery and annotation of gene elements is accomplished primarily by sequencing a diverse range of RNA sources, comparative genomics, integrative bioinformatic methods, and human curation. Regulatory elements are typically investigated through DNA hypersensitivity assays, assays of DNA methylation, and immunoprecipitation (IP) of proteins that interact with DNA and RNA, i.e., modified histones, transcription factors, chromatin regulators, and RNA-binding proteins, followed by sequencing.',
        'url': 'https://www.encodeproject.org',
    }
]


BASE_SEARCH_URL = 'https://www.encodeproject.org/search/'


DATASET_FILTERS = [
    ('type', 'Experiment'),
    ('status', 'released'),
    ('assay_title', 'polyA plus RNA-seq'),
    ('assay_title', 'total RNA-seq'),
    ('assay_title', 'polyA minus RNA-seq'),
    ('replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens'),
    ('replicates.library.biosample.donor.organism.scientific_name', 'Mus musculus'),
    ('assembly', 'GRCh38'),
    ('assembly', 'mm10'),
    ('files.file_type', 'tsv'),
    ('format', 'json'),
]


DATASET_FROM_TO_FIELD_MAP = {
    'accession': 'id',
}


EXPRESSION_IDS = [
    {
        'id': 'EXPID001',
        'description': 'All polyA plus RNA-seq samples in humans.',
        'filters': [
            ('file.assay_title', 'polyA plus RNA-seq'),
            ('dataset.replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens'),
        ]
    },
    {
        'id': 'EXPID002',
        'description': 'All total RNA-seq samples in humans.',
        'filters': [
            ('file.assay_title', 'total RNA-seq'),
            ('dataset.replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens'),
        ]
    },
    {
        'id': 'EXPID003',
        'description': 'All polyA minus RNA-seq samples in humans.',
        'filters': [
            ('file.assay_title', 'polyA minus RNA-seq'),
            ('dataset.replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens'),
        ]
    },
    {
        'id': 'EXPID004',
        'description': 'All polyA plus RNA-seq samples in mouse.',
        'filters': [
            ('file.assay_title', 'polyA plus RNA-seq'),
            ('dataset.replicates.library.biosample.donor.organism.scientific_name', 'Mus musculus'),
        ]
    },
    {
        'id': 'EXPID005',
        'description': 'All total RNA-seq samples in mouse.',
        'filters': [
            ('file.assay_title', 'total RNA-seq'),
            ('dataset.replicates.library.biosample.donor.organism.scientific_name', 'Mus musculus'),
        ]
    },
    {
        'id': 'EXPID006',
        'description': 'All polyA minus RNA-seq samples in mouse.',
        'filters': [
            ('file.assay_title', 'polyA minus RNA-seq'),
            ('dataset.replicates.library.biosample.donor.organism.scientific_name', 'Mus musculus'),
        ]
    },
    {
        'id': 'EXPID007',
        'description': 'polyA plus RNA-seq for EGFR, KRAS, ALK, CTCF, POMC, and EP300 genes in human lung tissue samples',
        'filters': [
            ('searchTerm', 'lung'),
            ('file.assay_title', 'polyA plus RNA-seq'),
            ('dataset.replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens'),
            ('gene.symbol', 'EGFR'),
            ('gene.symbol', 'KRAS'),
            ('gene.symbol', 'ALK'),
            ('gene.symbol', 'POMC'),
            ('gene.symbol', 'EP300'),
            ('gene.symbol', 'CTCF'),
            ('file.biosample_ontology.classification', 'tissue'),
        ]
    }
]


EXPRESSION_IDS_MAP = {
    expression_id['id']: expression_id
    for expression_id in EXPRESSION_IDS
}


EXPRESSION_LIST_FILTERS_MAP = {
    'sampleIDList': 'file.@id',
    'featureIDList': 'expression.gene_id',
    'featureNameList': 'gene.symbol'
}


TICKET_PATH = 'rnaget/expressions/bytes'


SERVICE_INFO = {
    'id': 'org.ga4gh.encodeproject',
    'name': 'ENCODE RNAget',
    'type': {
        'group': 'org.encodeproject',
        'artifact': 'rnaget',
        'version': '1.1.0'
    },
    'description': 'This service implements the GA4GH RNAget API for ENCODE data',
    'organization': {
        'name': 'ENCODE',
        'url': 'https://www.encodeproject.org'
    },
    'contactUrl': 'mailto:encode-help@lists.stanford.edu',
    'version': '0.0.2',
    'supported': {
        'projects': True,
        'studies': True,
        'expressions': True,
        'continuous': False
    }
}


BLOCK_IF_NONE_FILTERS = [
    'gene.symbol',
    'file.@id',
    'dataset.@id',
    'dataset.biosample_summary',
    'expression.gene',
    'searchTerm',
    'advancedQuery',
]


DEFAULT_EXPRESSION_ID = 'EXPID007'
