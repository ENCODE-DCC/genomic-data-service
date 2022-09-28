# example to use this script to delete files: python utils/update_database.py --delete ENCFF495KNO ENCFF028UPE
# example to index more files: python utils/update_database.py --index ENCFF495KNO ENCFF028UPE
# example to update metadata for residents: python utils/update_database.py --resident ENCFF495KNO ENCFF028UPE
import requests
from genomic_data_service.region_indexer_elastic_search import RegionIndexerElasticSearch
from genomic_data_service.region_indexer_task import metadata_doc
from genomic_data_service.region_indexer import dataset_accession, index_regulome_db, SUPPORTED_CHROMOSOMES, SUPPORTED_ASSEMBLIES, clean_up, FILE_REQUIRED_FIELDS, DATASET_REQUIRED_FIELDS
from opensearchpy import OpenSearch, RequestsHttpConnection
import argparse


ENCODE_URL = 'https://www.encodeproject.org/'
files = ['ENCFF495KNO', 'ENCFF028UPE', 'ENCFF373HKQ']
ES_ENDPOINT = 'https://localhost:9200/'
HOST = 'localhost'
PORT = 9200
RESIDENT = 'resident_regionsets/regulomedb/'
INDEXES = [
    'chr1/',
    'chr2/',
    'chr3/',
    'chr4/',
    'chr5/',
    'chr6/',
    'chr7/',
    'chr8/',
    'chr9/',
    'chr10/',
    'chr11/',
    'chr12/',
    'chr13/',
    'chr14/',
    'chr15/',
    'chr16/',
    'chr17/',
    'chr18/',
    'chr19/',
    'chr20/',
    'chr21/',
    'chr22/',
    'chrx/',
    'chry/',

]

auth = ('admin', 'admin')
es = OpenSearch(
    hosts=[{'host': HOST, 'port': PORT}],
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


def get_metadata(accession):
    data = {}
    try:
        url = ENCODE_URL + 'search/?accession=' + \
            accession + '&format=json&field=*&limit=all'
        data = requests.get(url).json()['@graph'][0]
    except:
        print(accession, 'is not found in Encode database')
    return data


def get_file_uuid(file_accession):
    metadata = get_metadata(file_accession)
    return metadata.get('uuid', None)


def delete_file_by_accession(file_accession):
    file_uuid = get_file_uuid(file_accession)
    if file_uuid:
        resident_regionsets_url = ES_ENDPOINT + RESIDENT + file_uuid + '?pretty'
        response = requests.delete(resident_regionsets_url)
        result = response.json().get('result', None)
        if result == 'not_found':
            print(file_accession, 'is not found in Regulome database')
        elif response.json().get('result', None) == 'deleted':
            print(file_accession, 'is deleted in residents index')
            is_fail = False
            for index in INDEXES:
                json_data = {
                    'query': {
                        'match': {
                            'uuid': file_uuid,
                        },
                    },
                }
                url = ES_ENDPOINT + index + '_delete_by_query'
                response = requests.post(url, headers={}, json=json_data)
                data = response.json()
                failures = data.get('failures', [])
                if failures:
                    is_fail = True
                    print('fail to delete', file_accession, 'on', index)
            if not is_fail:
                print(file_accession, 'is deleted in regions index')


def get_resident(file_accession):
    data = {}
    file_uuid = get_file_uuid(file_accession)
    if file_uuid:
        url = ES_ENDPOINT + RESIDENT + file_uuid + '?pretty'
        data = requests.get(url).json()
    return data


def delete_resident(file_accession):
    file_uuid = get_file_uuid(file_accession)
    if file_uuid:
        resident_regionsets_url = ES_ENDPOINT + RESIDENT + file_uuid + '?pretty'
        response = requests.delete(resident_regionsets_url)


def re_index_resident(file_accessions):
    is_re_index = True
    for file_accession in file_accessions:
        resident = get_resident(file_accession)
        if not resident or resident.get('found', None) == False:
            is_re_index = False
            if resident.get('found', None) == False:
                print(file_accession, 'is not found in Regulome database.')
            print('Abort. Please use a correct list of file accessions')
            break
    if is_re_index:
        for file_accession in file_accessions:
            resident = get_resident(file_accession)
            file_uuid = resident['_source']['uuid']
            chroms = resident['_source']['chroms']

            file_metadata = get_metadata(file_accession)
            file_metadata = clean_up(file_metadata, FILE_REQUIRED_FIELDS)
            dataset_acc = dataset_accession(file_metadata)
            dataset_metadata = get_metadata(dataset_acc)
            dataset_metadata = clean_up(
                dataset_metadata, DATASET_REQUIRED_FIELDS)

            metadata = metadata_doc(file_uuid, file_metadata, dataset_metadata)
            metadata['chroms'] = chroms
            delete_resident(file_accession)
            es.index(index='resident_regionsets', doc_type='regulomedb',
                     body=metadata, id=str(metadata['uuid']))


def add_files(accessions):
    RegionIndexerElasticSearch(
        HOST, PORT, SUPPORTED_CHROMOSOMES, SUPPORTED_ASSEMBLIES
    ).setup_indices()

    index_regulome_db(HOST, PORT, accessions, 'local', [])


def main():
    parser = argparse.ArgumentParser(
        description='updating genomic data service for testing.'
    )

    parser.add_argument(
        '--delete',
        nargs='+',
        help='delelte one or more files related docs from elasticsearch database')

    parser.add_argument(
        '--resident',
        nargs='+',
        help='reindex one or more residents for updated file and dataset metadata')

    parser.add_argument(
        '--index',
        nargs='+',
        help='Index one or more files in the existing elasticsearch database')
    args = parser.parse_args()
    if args.delete:
        for accession in args.delete:
            delete_file_by_accession(accession)
    elif args.resident:
        re_index_resident(args.resident)
    elif args.index:
        add_files(args.index)
    else:
        print('Please add an argument.')


if __name__ == '__main__':
    main()
