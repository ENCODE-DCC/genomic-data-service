import pytest


@pytest.mark.integration
def test_rnaseq_views_rnaget_search_quick(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search-quick/?type=RNAExpression')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 16
    assert r.json['@graph'][0]['expression']['tpm'] >= 0
    assert r.status_code == 200


@pytest.mark.integration
def test_rnaseq_views_rnaget_search_view(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search/?type=RNAExpression')
    assert '@graph' in r.json
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
    assert r.json['@type'] == ['RNAExpressionSearch']
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
def test_rnaseq_views_rnaget_search_view_no_results_raises_404(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search/?type=RNAExpression&searchTerm=no match term')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 0
    assert r.status_code == 404
    r = client.get('/rnaget-search/?type=RNAExpression&searchTerm=no match term&format=json')
    assert r.json['notification'] == 'No results found'
    assert len(r.json['@graph']) == 0
    assert r.status_code == 404
    r = client.get(
        '/rnaget-search/?type=RNAExpression&type=XYZ'
    )
    assert r.status_code == 400
    assert (
        r.json['message'] == "400 Bad Request: Invalid types: ['XYZ']"
    )


@pytest.mark.integration
def test_rnaseq_views_rnaget_report_view(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-report/?type=RNAExpression')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 16
    assert r.status_code == 200
    assert r.json['notification'] == 'Success'
    assert r.json['@type'] == ['RNAExpressionReport']
    assert r.json['clear_filters'] == '/rnaget-report/?type=RNAExpression'
    r = client.get('/rnaget-report/?type=RNAExpression&expression.tpm=gt:9.1&field=expression.tpm')
    assert len(r.json['@graph']) == 8
    r = client.get(
        '/rnaget-report/?type=RNAExpression&expression.tpm=gt:9.1&searchTerm=RNF19A'
    )
    assert len(r.json['@graph']) == 4
    r = client.get(
        '/rnaget-report/?type=RNAExpression&type=RNAExpression'
    )
    assert r.status_code == 400
    assert (
        r.json['message'] == "400 Bad Request: Report view requires specifying a single type: [('type', 'RNAExpression'), ('type', 'RNAExpression')]"
    )
    r = client.get(
        '/rnaget-report/?type=RNAExpression&type=XYZ'
    )
    assert r.status_code == 400
    assert (
        r.json['message'] == "400 Bad Request: Invalid types: ['XYZ']"
    )


@pytest.mark.integration
def test_rnaseq_views_rnaget_search_cached_facets_view(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-search/?type=RNAExpression')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 16
    assert r.json['@graph'][0]['expression']['tpm'] >= 0
    assert r.status_code == 200
    assert 'facets' in r.json
    assert len(r.json['facets']) == 7


@pytest.mark.integration
def test_rnaseq_views_rnaget_report_cached_facets_view(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget-report/?type=RNAExpression')
    assert '@graph' in r.json
    assert len(r.json['@graph']) == 16
    assert r.json['@graph'][0]['expression']['tpm'] >= 0
    assert r.status_code == 200
    assert 'facets' in r.json
    assert len(r.json['facets']) == 7


@pytest.mark.integration
def test_rnaseq_views_rnaget_rna_expression_search_generator(rnaseq_data_in_elasticsearch):
    from types import GeneratorType
    from genomic_data_service.rnaseq.searches import rna_expression_search_generator
    from genomic_data_service.searches.requests import make_search_request
    from genomic_data_service import app
    path = (
        '/dummy/?type=RNAExpression&searchTerm=RNF19A&field=expression.fpkm&field=gene.symbol'
    )
    with app.test_request_context(path=path):
        search_request = make_search_request()
        r = rna_expression_search_generator(search_request)
        assert isinstance(r['@graph'], GeneratorType)
        data = list(r['@graph'])
        assert len(data) == 4
        assert data[0]['expression']['fpkm'] >= 0
        assert data[0]['gene']['symbol'] == 'RNF19A'


@pytest.mark.integration
def test_rnaseq_views_rnaget_rna_expression_search_generator_manual_request(rnaseq_data_in_elasticsearch):
    from types import GeneratorType
    from genomic_data_service.rnaseq.searches import rna_expression_search_generator
    from genomic_data_service.searches.requests import make_search_request
    from genomic_data_service import app
    from flask import Request
    from snosearch.parsers import QueryString
    request = Request(
        {
            'PATH_INFO': '/dummy/',
            'QUERY_STRING': 'type=RNAExpression&searchTerm=RNF19A&field=expression.fpkm&field=gene.symbol',
        }
    )
    with app.app_context():
        search_request = make_search_request(request=request)
        r = rna_expression_search_generator(search_request)
        assert isinstance(r['@graph'], GeneratorType)
        data = list(r['@graph'])
        assert len(data) == 4
        assert data[0]['expression']['fpkm'] >= 0
        assert data[0]['gene']['symbol'] == 'RNF19A'
        qs = QueryString(search_request)
        qs.drop('field')
        qs.drop('limit')
        qs.extend(
            [
                ('field', 'expression.tpm'),
                ('field', 'file.@id'),
                ('limit', '2'),
            ]
        )
        assert qs.get_query_string() == (
            'type=RNAExpression&searchTerm=RNF19A&field=expression.tpm&field=file.%40id&limit=2'
        )
        new_request = qs.get_request_with_new_query_string()
        assert not hasattr(new_request, 'response')
        new_search_request = make_search_request(new_request)
        assert hasattr(new_search_request, 'registry')
        assert hasattr(new_search_request, 'response')
        r = rna_expression_search_generator(new_search_request)
        data = list(r['@graph'])
        assert len(data) == 2
        assert data[0]['expression']['tpm'] >= 0
        assert 'file' in data[0]


@pytest.mark.integration
def test_rnaseq_views_rnaget_expression_matrix_view(client, rnaseq_data_in_elasticsearch):
    from io import StringIO
    import csv
    r = client.get('/rnaget-expression-matrix/?type=RNAExpression')
    actual = list(
        csv.reader(
            StringIO(
                r.data.decode()
            ),
            delimiter='\t',
        )
    )
    expected = [
        [
            'featureID',
            'geneSymbol',
            '/files/ENCFF106SZG/, GM23338 originated from GM23248',
            '/files/ENCFF241WYH/, muscle of trunk tissue female embryo (113 days)',
            '/files/ENCFF273KTX/, uterus tissue female adult (53 years)',
            '/files/ENCFF730OTJ/, GM23338 originated from GM23248'
        ],
        ['ENSG00000039987.6', '', '0.01', '0.01', '0.01', '0.01'],
        ['ENSG00000055732.12', '', '0.27', '0.27', '0.27', '0.27'],
        ['ENSG00000060982.14', '', '10.18', '10.18', '10.18', '10.18'],
        ['ENSG00000034677.12', 'RNF19A', '9.34', '9.34', '9.34', '9.34']
    ]
    assert actual == expected
