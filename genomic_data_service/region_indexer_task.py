from celery import Celery
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk

from genomic_data_service.region_indexer_file_reader import S3BedFileRemoteReader


celery_app = Celery('regulome_indexer')
celery_app.config_from_object('config.celeryconfig')


RESIDENTS_INDEX = 'resident_regionsets'
FOR_REGULOME_DB = 'regulomedb'

# PEDRO TODO: import this from a centralized place
REGULOME_COLLECTION_TYPES = ['assay_term_name', 'annotation_type', 'reference_type']
REGULOME_DATASET_TYPES = ['experiment', 'annotation', 'reference']


SUPPORTED_CHROMOSOMES = [
    'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9',
    'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17',
    'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrX', 'chrY'
]

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


def index_settings():
    return {
        'index': {
            'number_of_shards': REGION_INDEXER_SHARDS,
            'max_result_window': SEARCH_MAX
        }
    }


def get_chrom_index_mapping(assembly_name='hg19'):
    return {
        assembly_name: {
            '_source': {
                'enabled': True
            },
            'properties': {
                'uuid': {
                    'type': 'keyword'
                },
                'coordinates': {
                    'type': 'integer_range'
                },
                'strand': {
                    'type': 'string'  # + - .
                },
                'value': {
                    'type': 'string'
                },
            }
        }
    }


def get_snp_index_mapping(chrom='chr1'):
    return {
        chrom: {
            '_all': {
                'enabled': False
            },
            '_source': {
                'enabled': True
            },
            'properties': {
                'rsid': {
                    'type': 'keyword'
                },
                'chrom': {
                    'type': 'keyword'
                },
                'coordinates': {
                    'type': 'integer_range'
                },
                'maf': {
                    'type': 'float',
                },
                'ref_allele_freq': {
                    'enabled': False,
                },
                'alt_allele_freq': {
                    'enabled': False,
                },
            }
        }
    }


def get_resident_mapping(use_type=FOR_REGULOME_DB):
    return {use_type: {"enabled": False}}


def add_to_residence(es, file_doc):
    uuid = file_doc['uuid']

    # Only splitting on doc_type=use in order to easily count them
    use_type = FOR_REGULOME_DB

    # Make sure there is an index set up to handle whether uuids are resident
    if not es.indices.exists(RESIDENTS_INDEX):
        es.indices.create(index=RESIDENTS_INDEX, body=index_settings())

    if not es.indices.exists_type(index=RESIDENTS_INDEX, doc_type=use_type):
        mapping = get_resident_mapping(use_type)
        es.indices.put_mapping(index=RESIDENTS_INDEX, doc_type=use_type,
                               body=mapping)

    es.index(index=RESIDENTS_INDEX, doc_type=use_type, body=file_doc, id=str(uuid))
    return True


def snps_bulk_iterator(snp_index, chrom, snps_for_chrom):
    for snp in snps_for_chrom:
        yield {'_index': snp_index, '_type': chrom, '_id': snp['rsid'], '_source': snp}


def index_snps(es, snps, metadata, chroms=None):
    assembly  = metadata['file']['assembly']
    snp_index = 'snp_' + assembly.lower()

    metadata['index'] = snp_index

    if not es.indices.exists(snp_index):
        es.indices.create(index=snp_index, body=index_settings())

    if chroms is None:
        chroms = list(snps.keys())

    for chrom in chroms:
        if len(snps[chrom]) == 0:
            continue

        if not es.indices.exists_type(index=snp_index, doc_type=chrom):
            mapping = get_snp_index_mapping(chrom)
            es.indices.put_mapping(index=snp_index, doc_type=chrom, body=mapping)

        bulk(es, snps_bulk_iterator(snp_index, chrom, snps[chrom]), chunk_size=500000)

        metadata['chroms'].append(chrom)

        try:
            es.indices.flush_synced(index=snp_index)
        except Exception:
            pass

    return True


def region_bulk_iterator(chrom, assembly, uuid, docs_for_chrom):
    for idx, doc in enumerate(docs_for_chrom):
        doc['uuid'] = uuid
        yield {'_index': chrom, '_type': assembly, '_id': uuid+'-'+str(idx), '_source': doc}


def index_regions(es, regions, metadata, chroms):
    uuid     = metadata['uuid']
    assembly = metadata['file']['assembly']

    if chroms is None:
        chroms = list(regions.keys())

    for chrom in list(regions.keys()):
        chrom_lc = chrom.lower()

        if not es.indices.exists(chrom_lc):
            es.indices.create(index=chrom_lc, body=index_settings())

        if not es.indices.exists_type(index=chrom_lc, doc_type=assembly):
            mapping = get_chrom_index_mapping(assembly)
            es.indices.put_mapping(index=chrom_lc, doc_type=assembly, body=mapping)

        if len(regions[chrom]) == 0:
            continue

        bulk(es, region_bulk_iterator(chrom_lc, assembly, uuid, regions[chrom]), chunk_size=500000)

        metadata['chroms'].append(chrom)

        try:
            es.indices.flush_synced(index=chrom)
        except Exception:
            pass

    return True


def index_regions_from_file(es, uuid, file_properties, dataset, snp=False):
    metadata = metadata_doc(uuid, file_properties, dataset)

    snp_set      = metadata.get('snps', False)
    dataset_type = metadata['dataset']['collection_type']
    regulome_strand = VALUE_STRAND_COL.get(dataset_type, {})

    metadata['chroms'] = []

    file_data = {}
    chroms = []

    readable_file = S3BedFileRemoteReader(file_properties, dataset_type, regulome_strand, snp_set=snp_set)

    if file_properties['file_format'] == 'bed':  # TODO: inspect this if. If format is not bed, it will fail for everything else, it should be placed in the beginning. Check that with Ben and Yunhai.
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

    return add_to_residence(es, metadata)


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
            'target': list_targets(dataset),
            'biosample_ontology': dataset.get('biosample_ontology', {}),
            'documents': []
        }
    }

    for prop in REGULOME_COLLECTION_TYPES:
        prop_value = dataset.get(prop)
        if prop_value:
            meta_doc['dataset'][prop] = prop_value
            if 'collection_type' not in meta_doc['dataset']:
                meta_doc['dataset']['collection_type'] = prop_value

    if meta_doc['dataset']['collection_type'] in ['Footprints', 'PWMs']:
        meta_doc['dataset']['documents'] = dataset.get('documents', [])

    biosample = dataset.get('biosample_ontology', {}).get('term_name', "None")
    if biosample:
        meta_doc['dataset']['biosample_term_name'] = biosample

    for dataset_type in REGULOME_DATASET_TYPES:
        if dataset_type in dataset['@type']:
            meta_doc['dataset_type'] = dataset_type
            break

    if dataset_type == 'Reference':
        meta_doc['snps'] = True

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


celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 2})
def index_file(uuid=None, file_properties=None, dataset=None, es_port=9201, es_hosts=['localhost'], force_reindex=False):
    es = Elasticsearch(port=es_port, hosts=es_hosts)
    
    indexed_file = file_in_es(uuid, es)

    if indexed_file:
        if force_reindex:
            remove_from_es(indexed_file, uuid, es)
        else:
            print("File " + uuid + " is already indexed")
            return

    index_regions_from_file(es, uuid, file_properties, dataset)

    import pdb; pdb.set_trace()

    print("File " + str(uuid) + " was indexed via " + file_properties['s3_uri'])

