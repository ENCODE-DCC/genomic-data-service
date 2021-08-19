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
    print('clearing rnaseq data')
    es.clear()


@pytest.fixture
def client():
    from genomic_data_service import app
    with app.test_client() as client:
        yield client


@pytest.mark.integration
def test_rnaseq_views_rnaget_search_quick(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search-quick/?type=RNAExpression')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 16
    assert r.json['@graph'][0]['expression']['tpm'] >= 0
    assert r.status_code == 200


@pytest.mark.integration
def test_rnaseq_views_rnaget_search(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search/?type=RNAExpression')
    assert '@graph' in r.json
    print({k: v for k, v in r.json.items() if k != '@graph'})
    print(r.json.keys())
    assert len(r.json['@graph']) == 16
    assert r.json['@graph'][0]['expression']['tpm'] >= 0
    assert r.status_code == 200
    expected_keys = [
        '@graph',
        '@id',
        '@type',
        'clear_filters',
        'columns',
        'facets',
        'filters',
        'notification',
        'sort',
        'title',
        'total'
    ]
    for expected_key in expected_keys:
        assert expected_key in r.json
    assert r.json['notification'] == 'Success'
    assert r.json['@id'] == '/rnaget-search/?type=RNAExpression'
    assert r.json['@type'] == ['RNAExpression']
    assert r.json['clear_filters'] == '/rnaget-search/?type=RNAExpression'
    assert r.json['columns'] == {
        '@id': {'title': 'ID'},
        'expression.gene_id': {'title': 'Feature ID'},
        'expression.tpm': {'title': 'TPM'},
        'expression.fpkm': {'title': 'FPKM'},
        'gene.symbol': {'title': 'Gene symbol'},
        'gene.name': {'title': 'Gene name'},
        'gene.title': {'title': 'Gene title'},
        'file.biosample_ontology.term_name': {'title': 'Biosample term name'},
        'file.assay_title': {'title': 'Assay title'},
        'file.assembly': {'title': 'Assembly'},
        'file.biosample_ontology.classification': {'title': 'Biosample classification'},
        'file.biosample_ontology.organ_slims': {'title': 'Biosample organ'},
        'dataset.replicates.library.biosample.sex': {'title': 'Biosample sex'},
        'dataset.replicates.library.biosample.donor.organism.scientific_name': {'title': 'Organism'},
        'dataset.biosample_summary': {'title': 'Biosample summary'},
        'expression_id': {'title': 'Expression ID'},
        'file.genome_annotation': {'title': 'Genome annotation'},
        'file.donors': {'title': 'Donors'},
        'file.@id': {'title': 'File'},
        'dataset.@id': {'title': 'Experiment'}
    }
    assert r.json['facets'] == [
        {
            'field': 'type',
            'title': 'Data Type',
            'terms': [
                {'key': 'RNAExpression', 'doc_count': 16}
            ],
            'total': 16,
            'type': 'terms',
            'appended': False,
            'open_on_load': False
        },
        {
            'field': 'file.assay_title',
            'title': 'Assay title',
            'terms': [
                {'key': 'total RNA-seq', 'doc_count': 12},
                {'key': 'polyA plus RNA-seq', 'doc_count': 4}
            ],
            'total': 16,
            'type': 'terms',
            'appended': False,
            'open_on_load': True
        },
        {
            'field': 'file.biosample_ontology.classification',
            'title': 'Biosample classification',
            'terms': [
                {'key': 'cell line', 'doc_count': 8},
                {'key': 'tissue', 'doc_count': 8}
            ],
            'total': 16,
            'type': 'terms',
            'appended': False,
            'open_on_load': True
        },
        {
            'field': 'file.biosample_ontology.term_name',
            'title': 'Biosample term name',
            'terms': [
                {'key': 'GM23338', 'doc_count': 8},
                {'key': 'muscle of trunk', 'doc_count': 4},
                {'key': 'uterus', 'doc_count': 4}
            ],
            'total': 16,
            'type': 'typeahead',
            'appended': False,
            'open_on_load': True
        },
        {
            'field': 'gene.symbol',
            'title': 'Gene symbol',
            'terms': [
                {'key': 'RNF19A', 'doc_count': 4}
            ],
            'total': 16,
            'type': 'typeahead',
            'appended': False,
            'open_on_load': True
        },
        {
            'field': 'file.assembly',
            'title': 'Assembly',
            'terms': [
                {'key': 'GRCh38', 'doc_count': 16}
            ],
            'total': 16,
            'type': 'terms',
            'appended': False,
            'open_on_load': True
        },
        {
            'field': 'dataset.replicates.library.biosample.donor.organism.scientific_name',
            'title': 'Organism',
            'terms': [
                {'key': 'Homo sapiens', 'doc_count': 16}
            ],
            'total': 16,
            'type': 'terms',
            'appended': False,
            'open_on_load': True
        },
        {
            'field': 'dataset.replicates.library.biosample.sex',
            'title': 'Biosample sex',
            'terms': [
                {'key': 'female', 'doc_count': 8},
                {'key': 'male', 'doc_count': 8}
            ],
            'total': 16,
            'type': 'terms',
            'appended': False,
            'open_on_load': False
        }
    ]
    assert r.json['filters'] == [{'field': 'type', 'term': 'RNAExpression', 'remove': '/rnaget-search/'}]
    assert r.json['sort'] == {
        'expression.tpm': {'order': 'desc', 'unmapped_type': 'keyword'},
        'gene.symbol': {'order': 'asc', 'unmapped_type': 'keyword'}
    }
    assert r.json['title'] == 'RNA expression search'
    assert r.json['total'] == 16


@pytest.mark.integration
def test_rnaseq_views_rnaget_search_no_results_raises_404(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search/?type=RNAExpression&searchTerm=no match term')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 0
    assert r.status_code == 404
    r = client.get('/rnaget-search/?type=RNAExpression&searchTerm=no match term&format=json')
    assert r.json['notification'] == 'No results found'
    assert len(r.json['@graph']) == 0
    assert r.status_code == 404
