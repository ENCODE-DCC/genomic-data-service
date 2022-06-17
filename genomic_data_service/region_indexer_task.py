from genomic_data_service import app
from celery import Celery
from pymongo import MongoClient

from genomic_data_service.file_opener import LocalFileOpener,S3FileOpener
from genomic_data_service.parser import SnfParser, RegionParser, FootPrintParser, PWMsParser
from genomic_data_service.constants import DATASET
from genomic_data_service.rnaseq.tests.fixtures import client
from genomic_data_service.strand import get_matrix_file_download_url, get_matrix_array, get_pwm
import uuid


def make_celery(app):
    celery_app = Celery(
        app.import_name
    )
    celery_app.conf.update(
        broker_url = app.config['CELERY_BROKER_URL'],
        task_serializer = app.config['CELERY_TASK_SERIALIZER'],
        result_serializer = app.config['CELERY_RESULT_SERIALIZER'],
        enable_utc = app.config['CELERY_ENABLE_UTC'], )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app

celery_app = make_celery(app)


RESIDENTS_INDEX = 'resident_regionsets'
FOR_REGULOME_DB = 'regulomedb'

# TODO: move constants to centralized file
REGULOME_COLLECTION_TYPES = ['assay_term_name', 'annotation_type', 'reference_type']


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

def get_cols_for_index(metadata):
    dataset_type = metadata['dataset']['collection_type'].lower()
    if dataset_type != 'eqtls':
        return INDEX_COLS.get(dataset_type, {})
    else:
        assembly = metadata['file']['assembly'].lower()
        return INDEX_COLS['eqtls'].get(assembly, {})

def add_to_residence(client, metadata):
    metadata['chroms'] = list(set(metadata['chroms']))
    metadata['_id'] = str(metadata['uuid'])
    client.gds.residents.insert_one(metadata)

    #es.index(index=RESIDENTS_INDEX, doc_type=FOR_REGULOME_DB, body=metadata, id=str(metadata['uuid']))


def snps_bulk_iterator(snp_index, chrom, snps_for_chrom):
    for snp in snps_for_chrom:
        yield {'_index': snp_index.lower(), '_type': chrom.lower(), '_id': snp['rsid'], '_source': snp}


def index_snps(client, snps, metadata, chroms=None):
    assembly  = metadata['file']['assembly']
    snp_collection = 'snp_' + assembly.lower()
    if chroms is None:
        chroms = list(snps.keys())

    for chrom in chroms:
        client.gds[snp_collection].insert_many(snps[chrom])
        

        

    return True


def region_bulk_iterator(chrom, assembly, uuid, docs_for_chrom):
    assembly = ASSEMBLIES_MAPPING.get(assembly, assembly).lower()

    for doc in docs_for_chrom:
        doc['uuid'] = uuid
        yield {'_index': chrom.lower(), '_type': assembly, '_source': doc}


def index_regions(client, regions, metadata, chroms):
    #uuid     = metadata['uuid']
    assembly = metadata['file']['assembly']
    for chrom in chroms:
        if chrom == 'chr1':
            client.gds[assembly + '_' + chrom].insert_many(regions[chrom])
        metadata['chroms'].append(chrom)
    

    return True


def index_regions_from_file(client, file_uuid, file_metadata, dataset_metadata, snp=False):
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
    elif "ensg_id_col" in cols_for_index:
        docs = RegionParser(reader, cols_for_index, file_path, gene_lookup=True).parse()
    elif file_metadata.get('annotation_type') == 'footprints' and file_metadata.get('assembly') == 'GRCh38':
        url = get_matrix_file_download_url(file_metadata['accession'])
        matrix = get_matrix_array(url)
        pwm = get_pwm(matrix)
        docs = FootPrintParser(reader, pwm, cols_for_index, file_path).parse()
    elif file_metadata.get('annotation_type') == 'PWMs' and file_metadata.get('assembly') == 'GRCh38':
        href = dataset_metadata["documents"][0]["attachment"]["href"]
        id = dataset_metadata["documents"][0]["@id"]
        matrix_file_download_url = "https://www.encodeproject.org" + id + href
        matrix = get_matrix_array(matrix_file_download_url)
        pwm = get_pwm(matrix)
        docs = PWMsParser(reader, pwm, cols_for_index, file_path).parse()
    else:
        docs = RegionParser(reader, cols_for_index, file_path).parse()

    if file_metadata['file_format'] == 'bed':
        for (chrom, doc) in docs:
            doc['uuid'] = metadata['uuid']
            if chrom.lower() not in SUPPORTED_CHROMOSOMES:
                continue

            if doc['coordinates']['gte'] == doc['coordinates']['lt']:
                print(
                    file_metadata['s3_uri'] + ' - on chromosome ' + doc[0] +
                    ', a start coordinate ' + doc[1] + ' is ' +
                    'larger than or equal to the end coordinate ' + doc[2] +', ' +
                    'skipping row'
                )
                continue  # Skip for 63 invalid peak in a non-ENCODE ChIP-seq result, exo_HelaS3.CTCF.bed.gz

            if (chrom not in file_data) or (len(file_data[chrom]) > MAX_SNP_BULK):
                # we are done with current chromosome and move on
                # 1 chrom at a time saves memory (but assumes the files are in chrom order!)
                if not file_opener.should_load_file_in_memory() and file_data and len(chroms) > 0:
                    if is_snp_reference:
                        #index_snps(client, file_data, metadata, list(file_data.keys()))
                        pass
                    else:
                        index_regions(client, file_data, metadata, list(file_data.keys()))
                    file_data = {}

                file_data[chrom] = []

                if len(chroms) == 0 or chroms[-1] != chrom:
                    chroms.append(chrom)

            file_data[chrom].append(doc)

        file_opener.close()

    if len(chroms) == 0 or not file_data:
        raise IOError('Error parsing file %s' % file_metadata['href'])

    if is_snp_reference:
        #index_snps(client, file_data, metadata, list(file_data.keys()))
        pass
    else:
        index_regions(client, file_data, metadata, list(file_data.keys()))

    if not file_opener.should_load_file_in_memory() and metadata['chroms'] != chroms:
        print(metadata['file']['@id'] + ' chromosomes ' + ('SNPs' if is_snp_reference else 'regions')  +' indexed out of order!')

    file_opener.close()

    add_to_residence(client, metadata)
    

def index_regions_from_test_snp_file(client, file_uuid, file_path, file_metadata):
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
                'larger than or equal to the end coordinate ' + doc[2] +', ' +
                'skipping row'
            )
            continue  # Skip for 63 invalid peak in a non-ENCODE ChIP-seq result, exo_HelaS3.CTCF.bed.gz

        if (chrom not in file_data) or (len(file_data[chrom]) > MAX_SNP_BULK):
            # we are done with current chromosome and move on
            # 1 chrom at a time saves memory (but assumes the files are in chrom order!)
            if file_data and len(chroms) > 0:
                #index_snps(client, file_data, metadata, list(file_data.keys()))
                
                file_data = {}

            file_data[chrom] = []

            if len(chroms) == 0 or chroms[-1] != chrom:
                chroms.append(chrom)

        file_data[chrom].append(doc)


    if len(chroms) == 0 or not file_data:
        raise IOError('Error parsing file %s' % file_path)

    #index_snps(client, file_data, metadata, list(file_data.keys()))

    add_to_residence(client, metadata)

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
                    target_labels.extend([gene['symbol'].upper() for gene in genes])

    return target_labels


def metadata_doc(file_uuid, file_metadata, dataset_metadata):
    meta_doc = {
        'uuid': file_uuid,
        'uses': FOR_REGULOME_DB,
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
        meta_doc['dataset']['documents'] = dataset_metadata.get('documents', [])

    return meta_doc


def remove_from_es(indexed_file, file_uuid, es):
    if not indexed_file:
        print("Trying to drop file: %s  NOT FOUND", file_uuid)
        return
    
    if 'index' in indexed_file:
        es.delete(index=indexed_file['index'])
    else:
        for chrom in indexed_file['chroms']:
            es.delete(index=chrom.lower(), doc_type=indexed_file['assembly'], id=str(file_uuid))

        es.delete(index=RESIDENTS_INDEX, doc_type=FOR_REGULOME_DB, id=str(file_uuid))
        
        return True

def remove_snp_from_es(snp_index, file_uuid, es):
    es.delete(index=snp_index)
    es.delete(index=RESIDENTS_INDEX, doc_type=FOR_REGULOME_DB, id=str(file_uuid))

def remove_region_from_es(file_uuid, assembly, es):
    for chrom in SUPPORTED_CHROMOSOMES:
        es.delete(index=chrom.lower(), doc_type=assembly, id=str(file_uuid))

    es.delete(index=RESIDENTS_INDEX, doc_type=FOR_REGULOME_DB, id=str(file_uuid))






@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 2})
def index_file(self, file_metadata, dataset_metadata, es_hosts, es_port, force_reindex=False):
    client = MongoClient()

    file_uuid = file_metadata['uuid']

    index_regions_from_file(client, file_uuid, file_metadata, dataset_metadata)

    return f"File {file_uuid} was indexed via {file_metadata['href']}"

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 2})
def index_local_snp_files(self, file_path, file_properties, es_hosts, es_port):
    client = MongoClient()
    id = str(uuid.uuid4())
    print("indexing local file ", file_path, id)
    index_regions_from_test_snp_file(client, id, file_path, file_properties)

    return f"File {file_path} was indexed"
