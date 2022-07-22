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

SEARCH_ENDPOINT = 'https://www.encodeproject.org/search/'
SUPPORTED_ASSEMBLIES = ['GRCh38', 'GRCh37', 'hg19', 'GRCm38', 'mm10']
ALLOWED_STATUSES = ['released']
ASSAY_TITLES = [
    'TF ChIP-seq',
    'DNase-seq',
    'ATAC-seq',
    'eCLIP',
    'RAMPAGE',
    'CAGE',
    'ChIA-PET'
]

ENCODE_QUERY = [
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
    'files.preferred_default=True',
    '&'.join([f'status={st}' for st in ALLOWED_STATUSES]),
    '&'.join([f'assembly={sa}' for sa in SUPPORTED_ASSEMBLIES]),
    'format=json',
    'limit=all'
]


def index_encode_files(query, requirements, ignore, dry_run=False):
    endpoint = f"{SEARCH_ENDPOINT}?{'&'.join(query)}"

    items = requests.get(endpoint).json()['@graph']

    accessions = []

    for item in items:
        files = item.get('files', [])

        for f in files:
            if f['accession'] in ignore:
                continue

            valid = True
            for requirement in requirements.keys():
                if f.get(requirement, '') not in requirements[requirement]:
                    valid = False

            if valid:
                accessions.append(f['accession'])

                if not dry_run:
                    index_file.delay(f, item, es_uri, es_port)

    return accessions


def encode_annotations(ignore=[], dry_run=False):
    requirements = {
        'file_format': ['bed']
    }

    query = [
        'type=Annotation',
        'encyclopedia_version=ENCODE+v5',
        'annotation_type=representative+DNase+hypersensitivity+sites'
    ] + ENCODE_QUERY

    accessions = index_encode_files(query, requirements, ignore, dry_run)

    query = [
        'type=Annotation',
        'encyclopedia_version=ENCODE+v5',
        'annotation_type=candidate+Cis-Regulatory+Elements',
        'annotation_subtype=all'
    ] + ENCODE_QUERY

    accessions_cis = index_encode_files(
        query, requirements, accessions + ignore, dry_run)

    return accessions + accessions_cis


def encode_functional_characterization_experiments(ignore=[], dry_run=False):
    requirements = {
        'file_format': ['bed'],
        'file_type': ['bed bed6+'],
        'preferred_default': [True]
    }

    query = [
        'type=FunctionalCharacterizationExperiment',
        'control_type!=*',
        'audit.WARNING.category!=lacking+processed+data',
        'files.file_type=bed+bed6%2B',
    ] + ENCODE_QUERY

    return index_encode_files(query, requirements, ignore, dry_run)


def encode_experiments(ignore=[], dry_run=False):
    requirements = {
        'file_format': ['bed'],
        'preferred_default': [True]
    }

    query = [
        'type=Experiment',
        '&'.join([f'assay_title={at}' for at in ASSAY_TITLES]),
        'files.file_format=bed'
    ] + ENCODE_QUERY

    return index_encode_files(query, requirements, ignore, dry_run)


def index_encode_region_search(dry_run=False):
    func_exps = encode_functional_characterization_experiments(dry_run=dry_run)
    annotations = encode_annotations(ignore=func_exps, dry_run=dry_run)
    return encode_experiments(ignore=func_exps + annotations, dry_run=dry_run)


if __name__ == '__main__':
    RegionIndexerElasticSearch(
        es_uri, es_port, SUPPORTED_CHROMOSOMES, SUPPORTED_ASSEMBLIES).setup_indices()

    index_encode_region_search()
