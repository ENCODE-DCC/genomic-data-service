GENOME_TO_ALIAS = {
    'GRCh37': 'hg19',
    'GRCh38': 'grch38',
    'hg19': 'hg19',
    'mm10': 'mm10',
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

ORGANS = ['adipose tissue', 'adrenal gland', 'arterial blood vessel', 'blood', 'blood vessel', 'bone element', 'bone marrow', 'brain', 'breast', 'colon', 'connective tissue', 'ear', 'embryo', 'endocrine gland', 'epithelium', 'esophagus', 'exocrine gland', 'extraembryonic component', 'eye', 'gonad', 'heart', 'immune organ', 'intestine', 'kidney', 'large intestine',
          'limb', 'liver', 'lung', 'lymph node', 'lymphoid tissue', 'mammary gland', 'mouth', 'musculature of body', 'nerve', 'ovary', 'pancreas', 'penis', 'placenta', 'prostate gland', 'skin of body', 'skin of prepuce of penis', 'small intestine', 'spinal cord', 'spleen', 'stomach', 'testis', 'thymus', 'thyroid gland', 'uterus', 'vagina', 'vasculature']

FREQ_SOURCES = ['bravo_af', 'gnomad_af_total']

CHR_GRCH38 = [
    'nc_000001.11',
    'nc_000002.12',
    'nc_000003.12',
    'nc_000004.12',
    'nc_000005.10',
    'nc_000006.12',
    'nc_000007.14',
    'nc_000008.11',
    'nc_000009.12',
    'nc_000010.11',
    'nc_000011.10',
    'nc_000012.12',
    'nc_000013.11',
    'nc_000014.9',
    'nc_000015.10',
    'nc_000016.10',
    'nc_000017.11',
    'nc_000018.10',
    'nc_000019.10',
    'nc_000020.11',
    'nc_000021.9',
    'nc_000022.11',
    'nc_000023.11',
    'nc_000024.10',
]
CHR_GRCH37 = [
    'nc_000001.10',
    'nc_000002.11',
    'nc_000003.11',
    'nc_000004.11',
    'nc_000005.9',
    'nc_000006.11',
    'nc_000007.13',
    'nc_000008.10',
    'nc_000009.11',
    'nc_000010.10',
    'nc_000011.9',
    'nc_000012.11',
    'nc_000013.10',
    'nc_000014.8',
    'nc_000015.9',
    'nc_000016.9',
    'nc_000017.10',
    'nc_000018.9',
    'nc_000019.9',
    'nc_000020.10',
    'nc_000021.9',
    'nc_000022.10',
    'nc_000023.10',
    'nc_000024.9',
]

CATALOG_API_FREQ = 'https://api-dev.catalog.igvf.org/api/variants/freq?page=0&maximum_af=1&limit=500'
CATALOG_API_VARIANTS = 'https://api-dev.catalog.igvf.org/api/variants?page=0&limit=500'
