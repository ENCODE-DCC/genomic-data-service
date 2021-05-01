from celery import Celery
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk

from genomic_data_service.region_indexer_file_reader import S3BedFileRemoteReader


celery_app = Celery('regulome_indexer')
celery_app.config_from_object('config.celeryconfig')


RESIDENTS_INDEX = 'resident_regionsets'
FOR_REGULOME_DB = 'regulomedb'

# TODO: move constants to centralized file
REGULOME_COLLECTION_TYPES = ['assay_term_name', 'annotation_type', 'reference_type']
REGULOME_DATASET_TYPES = ['Experiment', 'Annotation', 'Reference']


SUPPORTED_CHROMOSOMES = [
    'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9',
    'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17',
    'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrX', 'chrY'
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
VALUE_STRAND_COL = {
    'ChIP-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'DNase-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'FAIRE-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'chromatin state': {
        'value_col': 3
    },
    'eQTLs': {
        'value_col': 5
    },
    'Footprints': {
        'strand_col': 5,
    },
    'PWMs': {
        'strand_col': 4,
    },
}


def add_to_residence(es, file_doc):
    uuid = file_doc['uuid']

    use_type = FOR_REGULOME_DB

    es.index(index=RESIDENTS_INDEX, doc_type=use_type, body=file_doc, id=str(uuid))


def snps_bulk_iterator(snp_index, chrom, snps_for_chrom):
    for snp in snps_for_chrom:
        yield {'_index': snp_index.lower(), '_type': chrom.lower(), '_id': snp['rsid'], '_source': snp}


def index_snps(es, snps, metadata, chroms=None):
    assembly  = metadata['file']['assembly']
    snp_index = 'snp_' + assembly.lower()

    metadata['index'] = snp_index

    if chroms is None:
        chroms = list(snps.keys())

    for chrom in chroms:
        if len(snps[chrom]) == 0:
            continue

        bulk(es, snps_bulk_iterator(snp_index, chrom, snps[chrom]), chunk_size=100000, request_timeout=1000)

        metadata['chroms'].append(chrom)

    return True


def region_bulk_iterator(chrom, assembly, uuid, docs_for_chrom):
    assembly = ASSEMBLIES_MAPPING.get(assembly, assembly).lower()

    for idx, doc in enumerate(docs_for_chrom):
        doc['uuid'] = uuid
        yield {'_index': chrom.lower(), '_type': assembly, '_id': uuid+'-'+str(idx), '_source': doc}


def index_regions(es, regions, metadata, chroms):
    uuid     = metadata['uuid']
    assembly = metadata['file']['assembly']

    if chroms is None:
        chroms = list(regions.keys())

    for chrom in list(regions.keys()):
        chrom_lc = chrom.lower()

        if len(regions[chrom]) == 0:
            continue

        bulk(es, region_bulk_iterator(chrom_lc, assembly, uuid, regions[chrom]), chunk_size=100000, request_timeout=1000)
        metadata['chroms'].append(chrom)

    return True


def index_regions_from_file(es, uuid, file_properties, dataset, snp=False):
    metadata = metadata_doc(uuid, file_properties, dataset)

    snp_set      = dataset['@type'][0] == 'Reference'
    dataset_type = metadata['dataset']['collection_type']
    regulome_strand = VALUE_STRAND_COL.get(dataset_type, {})

    metadata['chroms'] = []

    file_data = {}
    chroms = []

    readable_file = S3BedFileRemoteReader(file_properties, dataset_type, regulome_strand, snp_set=snp_set)

    if file_properties['file_format'] == 'bed':
        for (chrom, doc) in readable_file.parse():
            if chrom not in SUPPORTED_CHROMOSOMES:
                continue

            if doc['coordinates']['gte'] == doc['coordinates']['lt']:
                print(
                    file_properties['s3_uri'] + ' - on chromosome ' + row[0] +
                    ', a start coordinate ' + row[1] + ' is ' +
                    'larger than or equal to the end coordinate ' + row[2] +', ' +
                    'skipping row'
                )
                continue  # Skip for 63 invalid peak in a non-ENCODE ChIP-seq result, exo_HelaS3.CTCF.bed.gz

            if (chrom not in file_data) or (len(file_data[chrom]) > MAX_SNP_BULK):
                # we are done with current chromosome and move on
                # 1 chrom at a time saves memory (but assumes the files are in chrom order!)
                if not readable_file.should_load_file_in_memory() and file_data and len(chroms) > 0:
                    if snp_set:
                        index_snps(es, file_data, metadata, list(file_data.keys()))
                    else:
                        index_regions(es, file_data, metadata, list(file_data.keys()))
                    file_data = {}

                file_data[chrom] = []

                if len(chroms) == 0 or chroms[-1] != chrom:
                    chroms.append(chrom)

            file_data[chrom].append(doc)

        readable_file.close()

    if len(chroms) == 0 or not file_data:
        raise IOError('Error parsing file %s' % file_properties['href'])

    if snp_set:
        index_snps(es, file_data, metadata, list(file_data.keys()))
    else:
        index_regions(es, file_data, metadata, list(file_data.keys()))

    if not readable_file.should_load_file_in_memory() and metadata['chroms'] != chroms:
        print(metadata['file']['@id'] + ' chromosomes ' + ('SNPs' if snp_set else 'regions')  +' indexed out of order!')

    readable_file.close()

    add_to_residence(es, metadata)


def list_targets(dataset):
    target_labels = []

    target = dataset.get('target', {})
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


def metadata_doc(uuid, file_properties, dataset):
    meta_doc = {
        'uuid': uuid,
        'uses': FOR_REGULOME_DB,
        'file': {
            'uuid': uuid,
            '@id': file_properties['@id'],
            'assembly': file_properties.get('assembly', 'unknown')
        },
        'dataset': {
            'uuid': dataset['uuid'],
            '@id': dataset['@id'],
            'target': [dataset.get('target', {}).get('name')],
            'biosample_ontology': dataset.get('biosample_ontology', {}),
            'biosample_term_name': dataset.get('biosample_ontology', {}).get('term_name'),
            'documents': []
        },
        'dataset_type': dataset['@type'][0]
    }

    for prop in REGULOME_COLLECTION_TYPES:
        prop_value = dataset.get(prop)
        if prop_value:
            meta_doc['dataset']['collection_type'] = prop_value

    if meta_doc['dataset']['collection_type'] in ['Footprints', 'PWMs']:
        meta_doc['dataset']['documents'] = dataset.get('documents', [])

    return meta_doc


def remove_from_es(indexed_file, uuid, es):
    if not indexed_file:
        print("Trying to drop file: %s  NOT FOUND", uuid)
        return
    
    if 'index' in indexed_file:
        es.delete(index=indexed_file['index'])
    else:
        for chrom in indexed_file['chroms']:
            es.delete(index=chrom.lower(), doc_type=indexed_file['assembly'], id=str(uuid))

        es.delete(index=RESIDENTS_INDEX, doc_type=use_type, id=str(uuid))
        
        return True


def file_in_es(uuid, es):
    try:
        return es.get(index=RESIDENTS_INDEX, id=str(uuid)).get('_source', {})
    except NotFoundError:
        return None
    except Exception:
        pass

    return None


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 2})
def index_file(self, file_, dataset, es_hosts, es_port, force_reindex=False):
    es = Elasticsearch(port=es_port, hosts=es_hosts)

    file_uuid = file_['uuid']

    indexed_file = file_in_es(file_uuid, es)

    if indexed_file:
        if force_reindex:
            remove_from_es(indexed_file, file_uuid, es)
        else:
            return f"File {file_uuid} is already indexed"

    index_regions_from_file(es, file_uuid, file_, dataset)

    return f"File {file_uuid} was indexed via {file_['href']}"

