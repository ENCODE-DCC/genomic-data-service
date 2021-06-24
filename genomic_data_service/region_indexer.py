from genomic_data_service.region_indexer_task import index_file
from genomic_data_service.region_indexer_elastic_search import RegionIndexerElasticSearch

import requests
import pickle

from os import environ


if 'ES' in environ:
    es_uri = [environ['ES']]
else:
    es_uri = ['localhost']
es_port = 9201


SUPPORTED_CHROMOSOMES = [
    'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9',
    'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17',
    'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrX', 'chrY'
]

ENCODE_DOMAIN = 'https://test.encodeproject.org'
REGULOME_ENCODE_ACCESSIONS_MAPPING_PATH = 'regulome_encode_accessions_mapping.pickle'
REGULOME_ACCESSIONS_PATH = 'regulome_accessions.pickle'
ENCODE_SNP = ['ENCFF904UCL', 'ENCFF578KDT']
SUPPORTED_ASSEMBLIES = ['hg19', 'GRCh38']
REGULOME_ALLOWED_STATUSES = ['released', 'archived']
REGULOME_COLLECTION_TYPES = ['assay_term_name', 'annotation_type', 'reference_type']
REGULOME_DATASET_TYPES = ['Experiment', 'Annotation', 'Reference']
REGULOME_REGION_REQUIREMENTS = {
    'chip-seq': {
        'output_type': ['optimal idr thresholded peaks'],
        'file_format': ['bed']
    },
    'binding sites': {
        'output_type': ['curated binding sites'],
        'file_format': ['bed']
    },
    'dnase-seq': {
        'output_type': ['peaks'],
        'file_type': ['bed narrowpeak'],
        'file_format': ['bed']
    },
    'faire-seq': {
        'file_type': ['bed narrowpeak'],
        'file_format': ['bed']
    },
    'chromatin state': {
        'file_format': ['bed']
    },
    'pwms': {
        'output_type': ['pwms'],
        'file_format': ['bed']
    },
    'footprints': {
        'output_type': ['footprints'],
        'file_format': ['bed']
    },
    'eqtls': {
        'file_format': ['bed']
    },
    'dsqtls': {
        'file_format': ['bed']
    },
    'curated snvs': {
        'output_type': ['curated snvs'],
        'file_format': ['bed']
    },
    'index': {
        'output_type': ['variant calls'],
        'file_format': ['bed']
    }
}

FILE_REQUIRED_FIELDS = [
    '@id',
    '@type',
    'uuid',
    'assembly',
    'accession',
    'dataset',
    'title',
    'target',
    'targets',
    'href',
    's3_uri',
    'status',
    'file_format',
    'file_type',
    'file_size',
    'output_type',
    'assay_term_name',
    'annotation_type',
    'reference_type'
]

DATASET_REQUIRED_FIELDS = [
    '@id',
    '@type',
    'uuid',
    'accession',
    'target',
    'targets',
    'biosample_ontology',
    'assay_term_name',
    'annotation_type',
    'reference_type',
    'biosample_ontology',
    'documents',
    'status'
]

def clean_up(obj, fields):
    clean_obj = {}
    keys = obj.keys()
    for key in keys:
        if key in fields:
            clean_obj[key] = obj[key]
    return clean_obj


# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def print_progress_bar (iteration, total, prefix = 'Progress:', suffix = 'Complete', decimals = 1, length = 80, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)

    if iteration == total:
        print()


def encode_graph(query):
    query += [
        'field=*',
        'limit=all',
        'format=json'
    ]

    endpoint = f"{ENCODE_DOMAIN}/search/?{'&'.join(query)}"
    return requests.get(endpoint).json()['@graph']


def needs_to_fetch_documents(dataset):
    documents_required_for = ['footprints', 'pwms']

    for prop in REGULOME_COLLECTION_TYPES:
        prop_value = dataset.get(prop)

        if not prop_value:
            return False

        if isinstance(prop_value, list):
            for p in [p.lower() for p in prop_value]:
                if p in documents_required_for:
                    return True
        elif prop_value.lower() in documents_required_for:
             return True

    return False


def fetch_documents(dataset):
    if not needs_to_fetch_documents(dataset):
        return

    documents = []
    for document_id in dataset.get('documents', []):
        endpoint = f"{ENCODE_DOMAIN}{document_id}?format=json"
        documents.append(requests.get(endpoint).json())

    dataset['documents'] = documents


def log(text, verbose=False):
    if verbose:
        print(text)


def filter_files(files):
    files_to_index = []
    for f in files:

        if f['assembly'] not in SUPPORTED_ASSEMBLIES:
            log(f"Invalid assembly: {f['assembly']}")
            continue

        if f['status'] not in REGULOME_ALLOWED_STATUSES:
            log(f"Invalid status: {f['status']}")
            continue

        if f['file_format'] != 'bed':
            log(f"Invalid file format: {f['file_format']}")
            continue

        requirements = None

        for collection_type in REGULOME_COLLECTION_TYPES:
            if collection_type in f:
                if isinstance(f[collection_type], list):
                    for ctype in f[collection_type]:
                        if ctype.lower() in REGULOME_REGION_REQUIREMENTS:
                            requirements = REGULOME_REGION_REQUIREMENTS.get(ctype.lower())
                            break
                else:
                    requirements = REGULOME_REGION_REQUIREMENTS.get(f[collection_type].lower())

                if requirements is None:
                    log(f'Unsupported {collection_type}: {f[collection_type]}')

        if requirements is None:
            continue

        for requirement in ['output_type', 'file_type', 'file_format']:
            if requirement in requirements and f[requirement].lower() not in requirements[requirement]:
                log(f'Requirement {requirement} not satisfied: {f[requirement]} - expected: {requirements[requirement]}')
                continue

        files_to_index.append(f)

    return files_to_index


def dataset_accession(f):
    if 'dataset' not in f:
        return None

    return f['dataset'].split('/')[2]


def fetch_datasets(files, datasets):
    fetch = []

    for f in files:
        accession = dataset_accession(f)

        if accession in datasets:
            continue

        fetch.append(accession)

    datasets_data = encode_graph([f'accession={c}' for c in fetch])

    for dataset in datasets_data:
        fetch_documents(dataset)
        datasets[dataset['accession']] = dataset


def index_regulome_db(filter_files=False):
    regulome_encode_accessions = pickle.load(open(REGULOME_ENCODE_ACCESSIONS_MAPPING_PATH, 'rb'))
    regulome_accessions = list(pickle.load(open(REGULOME_ACCESSIONS_PATH, 'rb')))

    encode_accessions = ENCODE_SNP + [regulome_encode_accessions[reg] for reg in regulome_accessions]

    datasets = {}

    per_request = 350
    chunks = [encode_accessions[i:i + per_request] for i in range(0, len(encode_accessions), per_request)]

    i = 0
    print_progress_bar(i, len(chunks))
    for chunk in chunks:
        i += 1
        print_progress_bar(i, len(chunks))

        files = encode_graph([f'accession={c}' for c in chunk])

        files_to_index = filter_files(files) if filter_files else files

        fetch_datasets(files_to_index, datasets)

        for f in files_to_index:
            dataset = datasets.get(dataset_accession(f))

            if dataset is None:
                print(f"========= No dataset {dataset_accession(f)} found for file {f['accession']}")
                continue

            index_file.delay(
                clean_up(f, FILE_REQUIRED_FIELDS),
                clean_up(dataset, DATASET_REQUIRED_FIELDS),
                es_uri,
                es_port
            )


if __name__ == "__main__":
    RegionIndexerElasticSearch(es_uri, es_port, SUPPORTED_CHROMOSOMES, SUPPORTED_ASSEMBLIES).setup_indices()

    index_regulome_db()
