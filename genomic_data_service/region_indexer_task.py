from genomic_data_service import app
from celery import Celery
from opensearchpy.exceptions import NotFoundError
from opensearchpy.helpers import bulk
from genomic_data_service.file_opener import LocalFileOpener, S3FileOpener
from genomic_data_service.parser import SnfParser, RegionParser, FootPrintParser, PWMsParser
from genomic_data_service.constants import DATASET
from genomic_data_service.strand import get_matrix_file_download_url, get_matrix_array, get_pwm
import uuid
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3


def make_celery(app):
    celery_app = Celery(
        app.import_name
    )
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        task_serializer=app.config['CELERY_TASK_SERIALIZER'],
        result_serializer=app.config['CELERY_RESULT_SERIALIZER'],
        enable_utc=app.config['CELERY_ENABLE_UTC'], )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


celery_app = make_celery(app)


FILES_INDEX = 'files'
PEAKS_INDEX_PRE = 'peaks_'
SNPS_INDEX_PRE = 'snps_'

# TODO: move constants to centralized file
REGULOME_COLLECTION_TYPES = ['assay_term_name',
                             'annotation_type', 'reference_type']


SUPPORTED_CHROMOSOMES = [
    'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9',
    'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17',
    'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrx', 'chry'
]

# TODO: refactor
ASSEMBLIES_MAPPING = {
    'grch37': 'hg19',
    'hg38': 'grch38'
}

# Max number of SNP docs hold in memory before putting into the index
MAX_SNP_BULK = 3e6

REGION_INDEXER_SHARDS = 2
SEARCH_MAX = 200

# Columns (0-based) for value and strand to be indexed - based on RegulomeDB
INDEX_COLS = {
    'chip-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'dnase-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'faire-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'chromatin state': {
        'value_col': 3
    },
    'eqtls': {
        'hg19': {
            'value_col': 5,
        },
        'grch38': {
            'name_col': 3,
            'ensg_id_col': 8,
            'p_value_col': 14,
            'effect_size_col': 15
        }
    },
    'footprints': {
        'strand_col': 5,
    },
    'pwms': {
        'strand_col': 4,
    },
}
auth = ('admin', 'admin')


def get_cols_for_index(metadata):
    dataset_type = metadata['dataset']['collection_type'].lower()
    if dataset_type != 'eqtls':
        return INDEX_COLS.get(dataset_type, {})
    else:
        assembly = metadata['file']['assembly'].lower()
        return INDEX_COLS['eqtls'].get(assembly, {})


def add_to_residence(es, metadata):
    metadata['chroms'] = list(set(metadata['chroms']))

    es.index(index=FILES_INDEX,
             body=metadata, id=str(metadata['uuid']))


def snps_bulk_iterator(snp_index, snps_for_chrom):
    for snp in snps_for_chrom:
        yield {'_index': snp_index, '_id': snp['rsid'], '_source': snp}


def index_snps(es, snps, metadata, chroms=None):
    assembly = metadata['file']['assembly']
    assembly = ASSEMBLIES_MAPPING.get(assembly, assembly).lower()

    if chroms is None:
        chroms = list(snps.keys())

    for chrom in chroms:
        if len(snps[chrom]) == 0:
            continue
        snp_index = SNPS_INDEX_PRE + assembly.lower()
        bulk(es, snps_bulk_iterator(
            snp_index, snps[chrom]), chunk_size=100000, request_timeout=2000)

        metadata['chroms'].append(chrom)

    return True


def peaks_bulk_iterator(peaks_index, uuid, docs_for_chrom):

    for doc in docs_for_chrom:
        doc['uuid'] = uuid
        yield {'_index': peaks_index, '_source': doc}


def index_peaks(es, regions, metadata, chroms):
    uuid = metadata['uuid']
    assembly = metadata['file']['assembly']
    assembly = ASSEMBLIES_MAPPING.get(assembly, assembly).lower()

    if chroms is None:
        chroms = list(regions.keys())

    for chrom in list(regions.keys()):

        if len(regions[chrom]) == 0:
            continue
        peaks_index = PEAKS_INDEX_PRE + assembly.lower() + '_' + chrom.lower()
        bulk(es, peaks_bulk_iterator(peaks_index, uuid,
             regions[chrom]), chunk_size=5000, request_timeout=2000)
        metadata['chroms'].append(chrom)

    return True


def index_peaks_from_file(es, file_uuid, file_metadata, dataset_metadata, snp=False):
    metadata = metadata_doc(file_uuid, file_metadata, dataset_metadata)
    is_snp_reference = dataset_metadata['@type'][0].lower() == 'reference'
    cols_for_index = get_cols_for_index(metadata)
    file_size = file_metadata.get('file_size', 0)
    file_path = file_metadata['s3_uri']
    metadata['chroms'] = []

    file_data = {}
    chroms = []
    file_opener = S3FileOpener(file_path, file_size)
    reader = file_opener.open()
    docs = None
    if is_snp_reference:
        docs = SnfParser(reader).parse()
    elif 'ensg_id_col' in cols_for_index:
        docs = RegionParser(reader, cols_for_index,
                            file_path, gene_lookup=True).parse()
    elif file_metadata.get('annotation_type') == 'footprints' and file_metadata.get('assembly') == 'GRCh38':
        url = get_matrix_file_download_url(dataset_metadata)
        matrix = get_matrix_array(url)
        pwm = get_pwm(matrix)
        docs = FootPrintParser(reader, pwm, cols_for_index, file_path).parse()
    elif file_metadata.get('annotation_type') == 'PWMs' and file_metadata.get('assembly') == 'GRCh38':
        href = dataset_metadata['documents'][0]['attachment']['href']
        id = dataset_metadata['documents'][0]['@id']
        matrix_file_download_url = 'https://www.encodeproject.org' + id + href
        matrix = get_matrix_array(matrix_file_download_url)
        pwm = get_pwm(matrix)
        docs = PWMsParser(reader, pwm, cols_for_index, file_path).parse()
    else:
        docs = RegionParser(reader, cols_for_index, file_path).parse()

    if file_metadata['file_format'] == 'bed':
        for (chrom, doc) in docs:
            if chrom.lower() not in SUPPORTED_CHROMOSOMES:
                continue

            if doc['coordinates']['gte'] == doc['coordinates']['lt']:
                print(
                    file_metadata['s3_uri'] + ' - on chromosome ' + doc[0] +
                    ', a start coordinate ' + doc[1] + ' is ' +
                    'larger than or equal to the end coordinate ' + doc[2] + ', ' +
                    'skipping row'
                )
                continue  # Skip for 63 invalid peak in a non-ENCODE ChIP-seq result, exo_HelaS3.CTCF.bed.gz

            if (chrom not in file_data) or (len(file_data[chrom]) > MAX_SNP_BULK):
                # we are done with current chromosome and move on
                # 1 chrom at a time saves memory (but assumes the files are in chrom order!)
                if not file_opener.should_load_file_in_memory() and file_data and len(chroms) > 0:
                    if is_snp_reference:
                        index_snps(es, file_data, metadata,
                                   list(file_data.keys()))
                    else:
                        index_peaks(es, file_data, metadata,
                                    list(file_data.keys()))
                    file_data = {}

                file_data[chrom] = []

                if len(chroms) == 0 or chroms[-1] != chrom:
                    chroms.append(chrom)

            file_data[chrom].append(doc)

        file_opener.close()

    if len(chroms) == 0 or not file_data:
        raise IOError('Error parsing file %s' % file_metadata['href'])

    if is_snp_reference:
        index_snps(es, file_data, metadata, list(file_data.keys()))
    else:
        index_peaks(es, file_data, metadata, list(file_data.keys()))

    if not file_opener.should_load_file_in_memory() and metadata['chroms'] != chroms:
        print(metadata['file']['@id'] + ' chromosomes ' +
              ('SNPs' if is_snp_reference else 'regions') + ' indexed out of order!')

    file_opener.close()

    add_to_residence(es, metadata)


def index_regions_from_test_snp_file(es, file_uuid, file_path, file_metadata):
    dateset_metadata = DATASET
    metadata = metadata_doc(file_uuid, file_metadata, dateset_metadata)
    metadata['chroms'] = []

    file_data = {}
    chroms = []

    file_opener = LocalFileOpener(file_path)
    reader = file_opener.open()
    docs = SnfParser(reader).parse()

    for (chrom, doc) in docs:
        if chrom.lower() not in SUPPORTED_CHROMOSOMES:
            continue

        if doc['coordinates']['gte'] == doc['coordinates']['lt']:
            print(
                file_path + ' - on chromosome ' + doc[0] +
                ', a start coordinate ' + doc[1] + ' is ' +
                'larger than or equal to the end coordinate ' + doc[2] + ', ' +
                'skipping row'
            )
            continue  # Skip for 63 invalid peak in a non-ENCODE ChIP-seq result, exo_HelaS3.CTCF.bed.gz

        if (chrom not in file_data) or (len(file_data[chrom]) > MAX_SNP_BULK):
            # we are done with current chromosome and move on
            # 1 chrom at a time saves memory (but assumes the files are in chrom order!)
            if file_data and len(chroms) > 0:
                index_snps(es, file_data, metadata, list(file_data.keys()))

                file_data = {}

            file_data[chrom] = []

            if len(chroms) == 0 or chroms[-1] != chrom:
                chroms.append(chrom)

        file_data[chrom].append(doc)

    if len(chroms) == 0 or not file_data:
        raise IOError('Error parsing file %s' % file_path)

    index_snps(es, file_data, metadata, list(file_data.keys()))

    add_to_residence(es, metadata)


def list_targets(dataset):
    target_labels = []

    target = dataset.get('target', dataset.get('targets'))
    if target:
        if isinstance(target, dict):
            target = [target]

        if isinstance(target, list):
            targets = target
            for target in targets:
                genes = target.get('genes')
                if genes:
                    target_labels.extend([gene['symbol'].upper()
                                         for gene in genes])

    return target_labels

# This is to catch files that are in ENCSR533BHN / PMID30650056. This may need to be updated if the metadata at ENCODE is improved.
# The ancestry info is stored in file aliases for now. It is the token after PMID.


def get_ancestry(file_metadata):
    ancestry = None
    aliases = file_metadata.get('aliases')
    if aliases:
        tag = aliases[0].split('-')[-1]
        if not tag.startswith('PMID'):
            ancestry = tag
    return ancestry


def get_files_for_genome_browser(dataset_metadata, assembly):
    files = dataset_metadata.get('files', [])
    files_for_genome_browser = []
    if files:
        if assembly == 'hg19':
            for file in files:
                if (
                    file.get('preferred_default', False)
                    and (file['file_format'] == 'bigBed' or file['file_format'] == 'bigWig')
                    and file.get('assembly') == 'hg19'
                    and file['status'] != 'revoked'
                ):
                    file_obj = get_file_obj_for_genome_browser(file)
                    files_for_genome_browser.append(file_obj)
        elif assembly == 'GRCh38':
            default_analysis_id = dataset_metadata['default_analysis']
            for file in files:
                if (
                    file.get('preferred_default', False)
                    and (file['file_format'] == 'bigBed' or file['file_format'] == 'bigWig')
                    and file.get('analyses', [])
                    and file['analyses'][0]['@id'] == default_analysis_id
                ):
                    file_obj = get_file_obj_for_genome_browser(file)
                    files_for_genome_browser.append(file_obj)
    return files_for_genome_browser


def get_file_obj_for_genome_browser(file):
    accession = file['accession']
    href = file.get('href')
    cloud_metadata = file.get('cloud_metadata')
    if cloud_metadata:
        cloud_metadata_url = cloud_metadata.get('url')
    return {
        'accession': accession,
        'href': href,
        'cloud_metadata_url': cloud_metadata_url
    }


def metadata_doc(file_uuid, file_metadata, dataset_metadata):
    meta_doc = {
        'uuid': file_uuid,
        'file': {
            'uuid': file_uuid,
            '@id': file_metadata['@id'],
            'assembly': file_metadata.get('assembly', 'unknown')
        },
        'dataset': {
            'uuid': dataset_metadata['uuid'],
            '@id': dataset_metadata['@id'],
            'target': list_targets(dataset_metadata),
            'biosample_ontology': dataset_metadata.get('biosample_ontology', {}),
            'biosample_term_name': dataset_metadata.get('biosample_ontology', {}).get('term_name'),
            'documents': [],
            'description': dataset_metadata.get('description'),
        },
        'dataset_type': dataset_metadata['@type'][0]
    }

    for prop in REGULOME_COLLECTION_TYPES:
        prop_value = dataset_metadata.get(prop)
        if prop_value:
            meta_doc['dataset']['collection_type'] = prop_value

    if meta_doc['dataset']['collection_type'].lower() in ['footprints', 'pwms']:
        meta_doc['dataset']['documents'] = dataset_metadata.get(
            'documents', [])
    if file_metadata.get('annotation_type') == 'caQTLs':
        ancestry = get_ancestry(file_metadata)
        if ancestry:
            meta_doc['file']['ancestry'] = ancestry
    # We only collect files info for genome browser for those three type of experiments
    if file_metadata.get('assay_term_name') in ['ChIP-seq', 'DNase-seq', 'FAIRE-seq']:
        files_for_genome_browser = get_files_for_genome_browser(
            dataset_metadata, file_metadata.get('assembly'))
        if files_for_genome_browser:
            meta_doc['dataset']['files_for_genome_browser'] = files_for_genome_browser

    return meta_doc


def file_in_es(file_uuid, es):
    try:
        return es.get(index=FILES_INDEX, id=str(file_uuid)).get('_source', {})
    except NotFoundError:
        return None
    except Exception:
        pass

    return None


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 2})
def index_file(self, file_metadata, dataset_metadata, host, port, opensearch_env='local'):
    if opensearch_env == 'local':
        auth = ('admin', 'admin')
    else:
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, 'us-west-2')
    es = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        # client_cert = client_cert_path,
        # client_key = client_key_path,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        #ca_certs = ca_certs_path
        connection_class=RequestsHttpConnection,
    )

    file_uuid = file_metadata['uuid']

    indexed_file = file_in_es(file_uuid, es)

    if indexed_file:
        return f'File {file_uuid} is already indexed'

    index_peaks_from_file(es, file_uuid, file_metadata, dataset_metadata)

    return f"File {file_uuid} was indexed via {file_metadata['href']}"


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 2})
def index_local_snp_files(self, file_path, file_properties, host, port, opensearch_env='local'):
    if opensearch_env == 'local':
        auth = ('admin', 'admin')
    else:
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, 'us-west-2')
    es = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        # client_cert = client_cert_path,
        # client_key = client_key_path,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        #ca_certs = ca_certs_path
        connection_class=RequestsHttpConnection,
    )
    id = uuid.uuid4()
    print('indexing local file ', file_path, id)
    index_regions_from_test_snp_file(es, id, file_path, file_properties)

    return f'File {file_path} was indexed'
