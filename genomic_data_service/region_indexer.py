from genomic_data_service.region_indexer_task import index_file
from genomic_data_service.region_indexer_elastic_search import RegionIndexerElasticSearch

import requests

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
        'file_type': ['bed narrowPeak'],
        'file_format': ['bed']
    },
    'faire-seq': {
        'file_type': ['bed narrowPeak'],
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


ENCODE_QUERY = [
    'internal_tags=RegulomeDB',
    'field=files',
    'field=biosample_ontology',
    'field=target.name',
    'field=biosample_term_name',
    'field=documents',
    'field=uuid',
    'field=assay_term_name',
    'field=annotation_type',
    'field=reference_type',
    'field=collection_type',
    '&'.join([f'status={st}' for st in REGULOME_ALLOWED_STATUSES]),
    'format=json',
    'limit=all'
]


def encode_graph(query):
    endpoint = f"https://www.encodeproject.org/search/?{'&'.join(query)}"

    return requests.get(endpoint).json()['@graph']


def fetch_reference_files_from_encode():
    query = ['type=Reference', 'internal_tags=RegulomeDB'] + ENCODE_QUERY

    reference_files = encode_graph(query)[0]

    for reference_file in reference_files.get('files', []):
        index_file.delay(reference_file, reference_files, es_uri, es_port)


def fetch_dataset_files_from_encode():
    query = ['type=Dataset', 'files.file_format=bed'] + ENCODE_QUERY

    dataset_files = encode_graph(query)

    for dataset_file in dataset_files:
        requirements = None
        
        for collection_type in REGULOME_COLLECTION_TYPES:
            if collection_type in dataset_file:
                requirements = REGULOME_REGION_REQUIREMENTS.get(dataset_file[collection_type].lower())

        if not requirements:
            print(f'{dataset_file["@id"]}')
            continue

        if dataset_file.get('files'):
            bed_file = dataset_file['files'][0] # TODO: change to preferred_default when ready

            for requirement in ['output_type', 'file_type']:
                if requirement in requirements and bed_file[requirement].lower() not in requirements[requirement]:
                    continue

            index_file.delay(bed_file, dataset_file, es_uri, es_port)


if __name__ == "__main__":
    RegionIndexerElasticSearch(es_uri, es_port, SUPPORTED_CHROMOSOMES, SUPPORTED_ASSEMBLIES).setup_indices()

    fetch_reference_files_from_encode()
    fetch_dataset_files_from_encode()
