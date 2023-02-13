from genomic_data_service.region_indexer_task import index_file, index_local_snp_files
from genomic_data_service.region_indexer_elastic_search import (
    RegionIndexerElasticSearch,
)
import requests
from requests.adapters import HTTPAdapter, Retry
import pickle
from genomic_data_service.constants import FILE_HG19
import argparse


SUPPORTED_CHROMOSOMES = [
    'chr1',
    'chr2',
    'chr3',
    'chr4',
    'chr5',
    'chr6',
    'chr7',
    'chr8',
    'chr9',
    'chr10',
    'chr11',
    'chr12',
    'chr13',
    'chr14',
    'chr15',
    'chr16',
    'chr17',
    'chr18',
    'chr19',
    'chr20',
    'chr21',
    'chr22',
    'chrX',
    'chrY',
]

ENCODE_DOMAIN = 'https://www.encodeproject.org'
ENCODE_ACCESSIONS_REGULOMEDB_2_0_HG19_PATH = 'file_accessions_regulomedb_2_0_hg19.pickle'
ENCODE_ACCESSIONS_REGULOMEDB_2_1_PATH = 'file_accessions_regulomedb_2_1.pickle'
ENCODE_ACCESSIONS_REGULOMEDB_2_2_PATH = 'file_accessions_regulomedb_2_2.pickle'
ENCODE_SNP = ['ENCFF904UCL', 'ENCFF578KDT']
SUPPORTED_ASSEMBLIES = ['hg19', 'GRCh38']
REGULOME_ALLOWED_STATUSES = ['released', 'archived']
REGULOME_COLLECTION_TYPES = ['assay_term_name',
                             'annotation_type', 'reference_type']
REGULOME_DATASET_TYPES = ['Experiment', 'Annotation', 'Reference']
TEST_SNP_FILE = 'snp_for_local_install.bed.gz'
TEST_ENCODE_ACCESSIONS_PATH = 'encode_accessions_for_local_install.pickle'

REGULOME_REGION_REQUIREMENTS = {
    'chip-seq': {
        'output_type': ['optimal idr thresholded peaks'],
        'file_format': ['bed'],
    },
    'binding sites': {'output_type': ['curated binding sites'], 'file_format': ['bed']},
    'dnase-seq': {
        'output_type': ['peaks'],
        'file_type': ['bed narrowpeak'],
        'file_format': ['bed'],
    },
    'faire-seq': {'file_type': ['bed narrowpeak'], 'file_format': ['bed']},
    'chromatin state': {'file_format': ['bed']},
    'pwms': {'output_type': ['pwms'], 'file_format': ['bed']},
    'footprints': {'output_type': ['footprints'], 'file_format': ['bed']},
    'eqtls': {'file_format': ['bed']},
    'caqtls': {'file_format': ['bed']},
    'curated snvs': {'output_type': ['curated snvs'], 'file_format': ['bed']},
    'index': {'output_type': ['variant calls'], 'file_format': ['bed']},
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
    'reference_type',
    'aliases',
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
    'assay_title',
    'annotation_type',
    'reference_type',
    'biosample_ontology',
    'documents',
    'replicates',
    'status',
    'files',
    'default_analysis',
]

TF_CHIP_SEQ_EXPS_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=Experiment&control_type!=*&status=released&assay_title=TF+ChIP-seq&assembly=GRCh38&field=files.accession&field=files.preferred_default&field=files.file_format&field=files.analyses.@id&field=default_analysis&format=json&limit=all'
DNASE_SEQ_EXPS_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=Experiment&control_type!=*&status=released&assay_title=DNase-seq&&assembly=GRCh38&field=files.accession&field=files.preferred_default&field=files.file_format&field=files.analyses.@id&field=default_analysis&format=json&limit=all'
ATAC_SEQ_EXPS_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=Experiment&control_type!=*&status=released&perturbed=false&assay_title=ATAC-seq&assembly=GRCh38&field=files.accession&field=files.preferred_default&field=files.file_format&field=files.analyses.@id&field=default_analysis&format=json&limit=all'
FOOTPRINT_ANNOTATIONS_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=Annotation&annotation_type=footprints&assembly=GRCh38&field=files.accession&format=json&limit=all'
PWM_ANNOTATIONS_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=Annotation&annotation_type=PWMs&assembly=GRCh38&field=files.accession&format=json&limit=all'
EQTL_ANNOTATIONS_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=Annotation&annotation_type=eQTLs&assembly=GRCh38&field=files.accession&format=json&limit=all'
CAQTL_ANNOTATIONS_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=Annotation&annotation_type=caQTLs&assembly=GRCh38&&field=files.accession&field=files.status&field=files.preferred_default&format=json&limit=all'
CHROMATIN_STATE_FILES_GRCH38_ENDPOINT = 'https://www.encodeproject.org/search/?type=File&output_type=semi-automated+genome+annotation&status=released&assembly=GRCh38&lab.title=Manolis+Kellis%2C+Broad&file_format=bed&format=json&limit=all'
HISTONE_CHIP_SEQ_EXPS_GRCH38_ENDPOINT = (
    'https://www.encodeproject.org/search/?control_type!=*&status=released&perturbed=false&assay_title=Histone+ChIP-seq&target.label=H3K27ac&target.label=H3K36me3&target.label=H3K4me3&target.label=H3K4me1&target.label=H3K27me3&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens&assembly=GRCh38&files.file_type=bed+narrowPeak&type=Experiment&files.analyses.status=released&files.preferred_default=true&limit=all&format=json'
    + '&field=files.accession&field=files.preferred_default&field=files.file_format&field=files.analyses.@id&field=default_analysis'
)

parser = argparse.ArgumentParser(
    description='indexing files for genomic data service.'
)

parser.add_argument(
    '--local', action='store_true',
    help='Index a small number of files for local install')

parser.add_argument(
    '--assembly', default=SUPPORTED_ASSEMBLIES, nargs='*',
    help='Index the files for the assemblies specified')

parser.add_argument(
    '--port', default=9201,
    help='Index a small number of files for local install')

parser.add_argument(
    '--uri', default=['localhost'], nargs='*',
    help='Index a small number of files for local install')

parser.add_argument(
    '--tag',
    help="Select 'RegulomeDB_2_0', 'RegulomeDB_2_1' or 'RegulomeDB_2_2' for internal_tags.",
    choices=['RegulomeDB_2_0', 'RegulomeDB_2_1', 'RegulomeDB_2_2'],
)

session = requests.Session()
retries = Retry(total=5, backoff_factor=1,
                status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))


def clean_up(obj, fields):
    clean_obj = {}
    keys = obj.keys()
    for key in keys:
        if key in fields:
            clean_obj[key] = obj[key]
    return clean_obj


# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def print_progress_bar(
    iteration,
    total,
    prefix='Progress:',
    suffix='Complete',
    decimals=1,
    length=80,
    fill='█',
    printEnd='\r',
):
    percent = ('{0:.' + str(decimals) + 'f}').format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)

    if iteration == total:
        print()


def encode_graph(query):
    query += ['field=*', 'limit=all', 'format=json']

    endpoint = f"{ENCODE_DOMAIN}/search/?{'&'.join(query)}"
    return session.get(endpoint).json()['@graph']


def need_to_fetch_documents(dataset):
    if type(dataset.get('documents')) is list:
        if dataset.get('documents') == [] or type(dataset.get('documents')[0]) is dict:
            return False

    documents_required_for = ['footprints', 'pwms']

    for prop in REGULOME_COLLECTION_TYPES:
        prop_value = dataset.get(prop)

        if not prop_value:
            continue

        if isinstance(prop_value, list):
            for p in [p.lower() for p in prop_value]:
                if p in documents_required_for:
                    return True
        elif prop_value.lower() in documents_required_for:
            return True

    return False


def fetch_documents(dataset):
    if not need_to_fetch_documents(dataset):
        return

    documents = []
    for document_id in dataset.get('documents', []):
        endpoint = f'{ENCODE_DOMAIN}{document_id}?format=json'
        documents.append(session.get(endpoint).json())

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
                            requirements = REGULOME_REGION_REQUIREMENTS.get(
                                ctype.lower()
                            )
                            break
                else:
                    requirements = REGULOME_REGION_REQUIREMENTS.get(
                        f[collection_type].lower()
                    )

                if requirements is None:
                    log(f'Unsupported {collection_type}: {f[collection_type]}')

        if requirements is None:
            continue

        for requirement in ['output_type', 'file_type', 'file_format']:
            if (
                requirement in requirements
                and f[requirement].lower() not in requirements[requirement]
            ):
                log(
                    f'Requirement {requirement} not satisfied: {f[requirement]} - expected: {requirements[requirement]}'
                )
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
        if accession in fetch:
            continue

        fetch.append(accession)

    datasets_data = encode_graph([f'accession={c}' for c in fetch])

    for dataset in datasets_data:
        fetch_documents(dataset)
        datasets[dataset['accession']] = dataset


def read_local_accessions_from_pickle(pickle_path):
    encode_accessions = list(pickle.load(open(pickle_path, 'rb')))
    return encode_accessions


def is_preferred_default_bed_from_default_analysis(default_analysis_id, file):
    return file.get('preferred_default', None) and file['file_format'] == 'bed' and file.get('analyses', []) and file['analyses'][0]['@id'] == default_analysis_id


def get_caQTL_preferred_default_file_accession(files):
    for file in files:
        if file.get('preferred_default', False) and file['status'] == 'released':
            return file['accession']
    return None


def make_pickle_file(encode_accessions):
    with open('file_accessions_in_es.pickle', 'wb') as file:
        pickle.dump(encode_accessions, file)


def get_encode_accessions_from_portal():
    encode_accessions = []
    # get files in experiment TF ChIP-seq using assembly GRCh38
    experiments = session.get(
        TF_CHIP_SEQ_EXPS_GRCH38_ENDPOINT).json()['@graph']
    # get files in experiment DNase-seq using assembly GRCh38
    experiments.extend(session.get(
        DNASE_SEQ_EXPS_GRCH38_ENDPOINT).json()['@graph'])
    # get files in experiment ATAC-seq using assembly GRCh38
    experiments.extend(session.get(
        ATAC_SEQ_EXPS_GRCH38_ENDPOINT).json()['@graph'])
    # get files in experiment histone ChIP-seq using assembly GRCh38
    experiments.extend(session.get(
        HISTONE_CHIP_SEQ_EXPS_GRCH38_ENDPOINT).json()['@graph'])
    # get files in footprints
    annotations = session.get(
        FOOTPRINT_ANNOTATIONS_GRCH38_ENDPOINT).json()['@graph']
    # get files in PWMs
    annotations.extend(session.get(
        PWM_ANNOTATIONS_GRCH38_ENDPOINT).json()['@graph'])
    # get files in eQTLs
    annotations.extend(session.get(
        EQTL_ANNOTATIONS_GRCH38_ENDPOINT).json()['@graph'])
    # get files for chromatin state for grch38
    chromatin_state_files = session.get(
        CHROMATIN_STATE_FILES_GRCH38_ENDPOINT).json()['@graph']
    # get ds_qtl annotations for grch38
    ds_qtls = session.get(CAQTL_ANNOTATIONS_GRCH38_ENDPOINT).json()['@graph']

    for experiment in experiments:
        files = experiment.get('files', [])
        default_analysis_id = experiment.get('default_analysis')
        if default_analysis_id:
            for file in files:
                if is_preferred_default_bed_from_default_analysis(default_analysis_id, file):
                    encode_accessions.append(file['accession'])

    for annotation in annotations:
        files = annotation.get('files', [])
        for file in files:
            encode_accessions.append(file['accession'])

    for file in chromatin_state_files:
        encode_accessions.append(file['accession'])

    for ds_qtl in ds_qtls:

        files = ds_qtl.get('files', [])
        if files:
            preferred_default_file_accession = get_caQTL_preferred_default_file_accession(
                files)
            if preferred_default_file_accession:
                encode_accessions.append(preferred_default_file_accession)
            else:
                for file in files:
                    if file['status'] == 'released':
                        encode_accessions.append(file['accession'])
    return encode_accessions


def get_encode_accessions_from_tag(tag):
    encode_accessions = []
    if tag == 'RegulomeDB_2_0':
        encode_accessions = read_local_accessions_from_pickle(
            pickle_path=ENCODE_ACCESSIONS_REGULOMEDB_2_0_HG19_PATH)
    elif tag == 'RegulomeDB_2_1':
        encode_accessions = read_local_accessions_from_pickle(
            pickle_path=ENCODE_ACCESSIONS_REGULOMEDB_2_1_PATH)
    elif tag == 'RegulomeDB_2_2':
        encode_accessions = read_local_accessions_from_pickle(
            pickle_path=ENCODE_ACCESSIONS_REGULOMEDB_2_2_PATH)
    return encode_accessions


def index_regulome_db(es_uri, es_port, encode_accessions, local_files=None, filter_files=False, per_request=350):
    print('Number of files for indexing from ENCODE:', len(encode_accessions))
    datasets = {}
    chunks = [
        encode_accessions[i: i + per_request]
        for i in range(0, len(encode_accessions), per_request)
    ]
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
                print(
                    f"========= No dataset {dataset_accession(f)} found for file {f['accession']}"
                )
                continue
            index_file.delay(
                clean_up(f, FILE_REQUIRED_FIELDS),
                clean_up(dataset, DATASET_REQUIRED_FIELDS),
                es_uri,
                es_port,
            )
    if local_files:
        for file in local_files:
            index_local_snp_files.delay(
                file['file_path'], file['file_metadata'], es_uri, es_port)


if __name__ == '__main__':

    args = parser.parse_args()
    es_uri = args.uri
    es_port = args.port
    is_local_install = args.local
    assemblies = args.assembly
    tag = args.tag
    print('es uri:', es_uri)
    print('es port:', es_port)

    RegionIndexerElasticSearch(
        es_uri, es_port, SUPPORTED_CHROMOSOMES, SUPPORTED_ASSEMBLIES
    ).setup_indices()

    if tag:
        encode_accessions = get_encode_accessions_from_tag(tag)
        index_regulome_db(es_uri, es_port, encode_accessions)
    elif not is_local_install:
        encode_accessions = []
        for assembly in assemblies:
            if assembly == 'hg19':
                encode_accessions.extend(read_local_accessions_from_pickle(
                    pickle_path=ENCODE_ACCESSIONS_REGULOMEDB_2_0_HG19_PATH))
            elif assembly == 'GRCh38':
                encode_accessions.extend(get_encode_accessions_from_portal())
            else:
                raise ValueError(f'Invalid assembly: {assembly}')
        make_pickle_file(encode_accessions)
        index_regulome_db(es_uri, es_port, encode_accessions)
    else:
        encode_accessions = list(pickle.load(
            open(TEST_ENCODE_ACCESSIONS_PATH, 'rb')))
        local_files = [
            {
                'file_path': TEST_SNP_FILE,
                'file_metadata': FILE_HG19
            }
        ]
        index_regulome_db(es_uri, es_port, encode_accessions, local_files)
