import pytest


@pytest.fixture()
def rnaseq_data_in_elasticsearch(mocker, mock_portal, raw_expressions, elasticsearch_client):
    from genomic_data_service.rnaseq.repository.elasticsearch import Elasticsearch
    mocker.patch(
        'genomic_data_service.rnaseq.domain.file.get_expression_generator',
        return_value=raw_expressions,
    )
    es = Elasticsearch(
        elasticsearch_client
    )
    files = mock_portal.get_rna_seq_files()
    print('loading rnaseq data')
    es.bulk_load_from_files(files)
    es._refresh()
    print('yielding')
    yield


@pytest.fixture
def client():
    from genomic_data_service import app
    with app.test_client() as client:
        yield client


def test_rnaseq_views_rnaget_search(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search/?type=RNAExpression')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 16
    assert r.json['@graph'][0]['expression']['tpm'] >= 0
    assert r.status_code == 200
