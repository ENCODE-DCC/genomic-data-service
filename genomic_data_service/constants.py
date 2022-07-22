GENOME_TO_ALIAS = {
    'GRCh37': 'hg19',
    'GRCh38': 'grch38',
    'hg19': 'hg19',
    'mm10': 'mm10',
    'hg19': 'hg19',
}

GENOME_TO_SPECIES = {
    'GRCh37': 'homo_sapiens',
    'GRCh38': 'homo_sapiens',
    'GRCm39': 'mouse',
    'GRCm38': 'mouse',
    'GRCm37': 'mouse',
    'NCBIM37': 'mouse',
}

ENSEMBL_URL = 'http://rest.ensembl.org/'
ENSEMBL_URL_GRCH37 = 'http://grch37.rest.ensembl.org/'


FILE_CH38 = {'@id': '/files/ENCFF904UCL/',
             'assembly': 'GRCh38', 'file_format': 'bed'}

FILE_HG19 = {'@id': '/files/ENCFF578KDT/',
             'assembly': 'hg19', 'file_format': 'bed'}

DATASET = {
    'uuid': '19b2ffe1-a645-4da5-ac4e-631f1629dca0',
    '@id': '/references/ENCSR942EOJ/',
    'target': [],
    'biosample_ontology': {},
    'biosample_term_name': None,
    'reference_type': 'index',
    '@type': ['Reference', 'FileSet', 'Dataset', 'Item'],
}

TWO_BIT_HG38_FILE_PATH = 'ml_models/two_bit_files/hg38.2bit'
TWO_BIT_HG19_FILE_PATH = 'ml_models/two_bit_files/hg19.2bit'
REGULOME_VALID_ASSEMBLY = ['GRCh37', 'GRCh38', 'hg19']
