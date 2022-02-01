import pytest

from genomic_data_service.region_indexer import dataset_accession

def test_indices(regulome_elasticsearch_client_index):
    
    indices = list(regulome_elasticsearch_client_index.es.indices.get_alias().keys())
    indices.sort()
    assert indices == ['chr1', 'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19',\
         'chr2', 'chr20', 'chr21', 'chr22',  'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chrx', 'chry', \
         'resident_regionsets', 'snp_grch38', 'snp_hg19',]


def test_index_regions(regulome_elasticsearch_client_index):
    from genomic_data_service.region_indexer_task import index_regions_from_file
    from genomic_data_service.region_indexer import encode_graph
    
    query = ['accession=ENCFF760LBY']

    file_properties = encode_graph(query)[0]
    file_uuid = file_properties['uuid']
    dataset_accession = file_properties['dataset'].split('/')[2]
    dataset_accession = 'accession=' + dataset_accession
    dataset_query = [dataset_accession]
    dataset = encode_graph(dataset_query)[0]
    #indexed_file = file_in_es(uuid, regulome_elasticsearch_client.es)
    index_regions_from_file(regulome_elasticsearch_client_index.es, file_uuid, file_properties, dataset, snp=False)

    regulome_elasticsearch_client_index.es.indices.refresh()

    result = regulome_elasticsearch_client_index.es.search(index="chr10", body={"query":{"match_all":{}}})
    assert result['hits']['total'] == 18014
    assert 'coordinates' in result['hits']['hits'][0]["_source"]
    assert 'strand' in result['hits']['hits'][0]["_source"]
    assert 'value' in result['hits']['hits'][0]["_source"]
    assert 'uuid' in result['hits']['hits'][0]["_source"]

    result = regulome_elasticsearch_client_index.es.search(index="resident_regionsets", body={"query":{"match_all":{}}})

    assert result['hits']['total'] == 1
    assert result['hits']['hits'][0]["_source"]['file']['uuid'] == file_uuid
    assert 'chroms' in result['hits']['hits'][0]["_source"]
    assert 'dataset' in result['hits']['hits'][0]["_source"]
    assert 'dataset_type' in result['hits']['hits'][0]["_source"]
    assert 'uuid' in result['hits']['hits'][0]["_source"]
    assert 'file' in result['hits']['hits'][0]["_source"]
    assert 'uses' in result['hits']['hits'][0]["_source"]

def test_index_snps(regulome_elasticsearch_client_index):
    
    import uuid
    from genomic_data_service.region_indexer_task import index_regions_from_test_snp_file
    from genomic_data_service.region_indexer import TEST_SNP_FILE, FILE_HG19

    file_uuid = uuid.uuid4()
    index_regions_from_test_snp_file(regulome_elasticsearch_client_index.es, file_uuid, TEST_SNP_FILE, FILE_HG19)
    regulome_elasticsearch_client_index.es.indices.refresh()
    result = regulome_elasticsearch_client_index.es.search(index="snp_hg19", body={"query":{"match_all":{}}})
    
    assert result['hits']['total'] == 11
    assert result['hits']['hits'][0]["_type"] == 'chr10'
    assert 'alt_allele_freq' in result['hits']['hits'][0]["_source"]
    assert 'ref_allele_freq' in result['hits']['hits'][0]["_source"]
    assert 'coordinates' in result['hits']['hits'][0]["_source"]
    assert 'rsid' in result['hits']['hits'][0]["_source"]
    assert 'chrom' in result['hits']['hits'][0]["_source"]
    assert 'maf' in result['hits']['hits'][0]["_source"]

    
