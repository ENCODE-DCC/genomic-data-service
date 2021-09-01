import pytest


def test_rnaseq_rnaget_mapping_map_fields():
    from genomic_data_service.rnaseq.rnaget.mapping import map_fields
    item = {
        'a': 1,
        'b': 2,
        'c': 3,
    }
    from_to_field_map = {
        'c': 'x'
    }
    assert map_fields(item, from_to_field_map) == {'x': 3, 'a': 1, 'b': 2}
    from_to_field_map = {
        'c': 'y',
        't': 'b',
        'a': 'abc',
    }
    assert map_fields(item, from_to_field_map) == {'y': 3, 'abc': 1, 'b': 2}
    item = {
        '@id': 'xyz',
    }
    from_to_field_map = {
        '@id': 'id',
    }
    assert map_fields(item, from_to_field_map) == {'id': 'xyz'}


def test_rnaseq_rnaget_mapping_convert_facet_to_filter():
    from genomic_data_service.rnaseq.rnaget.mapping import convert_facet_to_filter
    facet = {
        'field': 'target.label',
        'title': 'Target of assay',
        'terms': [
            {
                'key': 'HLH54F',
                'doc_count': 3
            },
            {
                'key': 'zfh2',
                'doc_count': 3
            }
        ],
        'total': 783,
    }
    expected_filter = {
        'filter': 'target.label',
        'description': 'Target of assay',
        'values': [
            'HLH54F',
            'zfh2',
        ]
    }
    assert convert_facet_to_filter(facet) == expected_filter


def test_rnaseq_rnaget_mapping_convert_list_filters_to_expression_filters():
    from genomic_data_service.rnaseq.rnaget.mapping import convert_list_filters_to_expression_filters
    from snosearch.parsers import QueryString
    from snosearch.adapters.flask.requests import RequestAdapter
    from flask import Request
    r = Request(
        {
            'QUERY_STRING': (
                'format=tsv'
                '&sampleIDList=/files/ENCFF1/,/files/ENCFF2/'
                '&featureIDList=ENSG1, ENSG2, ENSG3'
                '&featureNameList=CTCF,POMC'
            )
        }
    )
    qs = QueryString(RequestAdapter(r))
    assert qs.get_query_string() == (
        'format=tsv'
        '&sampleIDList=%2Ffiles%2FENCFF1%2F%2C%2Ffiles%2FENCFF2%2F'
        '&featureIDList=ENSG1%2C+ENSG2%2C+ENSG3'
        '&featureNameList=CTCF%2CPOMC'
    )
    qs = convert_list_filters_to_expression_filters(qs)
    assert qs.get_query_string() == (
        'format=tsv'
        '&file.%40id=%2Ffiles%2FENCFF1%2F&file.%40id=%2Ffiles%2FENCFF2%2F'
        '&expression.gene_id=ENSG1&expression.gene_id=ENSG2&expression.gene_id=ENSG3'
        '&gene.symbol=CTCF&gene.symbol=POMC'
    )


@pytest.mark.integration
def test_rnaseq_rnaget_projects_view(client):
    r = client.get('/rnaget/projects')
    assert r.status_code == 200
    project = r.json[0]
    fields = [
        'id',
        'name',
        'description',
        'url'
    ]
    for field in fields:
        assert field in project, field
    assert project['id'] == 'ENCODE'


@pytest.mark.integration
def test_rnaseq_rnaget_project_by_id_view(client):
    r = client.get('/rnaget/projects/ENCODE')
    assert r.status_code == 200
    project = r.json[0]
    fields = [
        'id',
        'name',
        'description',
        'url'
    ]
    for field in fields:
        assert field in project, field
    assert project['id'] == 'ENCODE'



@pytest.mark.integration
def test_rnaseq_rnaget_project_by_id_not_found_view(client):
    r = client.get('/rnaget/projects/NOTENCODE')
    assert r.status_code == 404
    assert r.json['message'] == '404 Not Found: Project not found'


@pytest.mark.integration
def test_rnaseq_rnaget_project_filters(client):
    r = client.get('/rnaget/projects/filters')
    assert r.status_code == 200
    assert r.json == []


@pytest.mark.integration
def test_rnaseq_rnaget_studies_view(client):
    r = client.get('/rnaget/studies')
    assert r.status_code == 200
    assert len(r.json) == 25
    r = client.get('/rnaget/studies?limit=2')
    assert len(r.json) == 2
    assert 'id' in r.json[0]
    assert '@id' in r.json[0]
    assert 'accession' not in r.json[0]
    r = client.get('/rnaget/studies?limit=1&field=description')
    assert len(r.json) == 1
    assert 'description' in r.json[0]


@pytest.mark.integration
def test_rnaseq_rnaget_study_by_id_view(client):
    r = client.get('/rnaget/studies/ENCSR558SEE')
    assert r.status_code == 200
    assert len(r.json) == 1
    assert r.json[0]['id'] == 'ENCSR558SEE'


@pytest.mark.integration
def test_rnaseq_rnaget_study_by_id_view_not_found(client):
    r = client.get('/rnaget/studies/NOTANID')
    assert r.status_code == 404
    assert r.json['message'] == '404 Not Found: Study not found'


@pytest.mark.integration
def test_rnaseq_rnaget_study_by_id_view(client):
    r = client.get('/rnaget/studies/filters')
    assert r.status_code == 200
    assert len(r.json) == 35
    assert r.json[1] == {
        'description': 'Assay type',
        'filter': 'assay_slims',
        'values': ['Transcription']
    }
    assert r.json[4] == {
        'description': 'Perturbation',
        'filter': 'perturbed',
        'values': [0, 1]
    }
    assert r.json[5] == {
        'description': 'Organism',
        'filter': 'replicates.library.biosample.donor.organism.scientific_name',
        'values': ['Homo sapiens', 'Mus musculus']
    }


@pytest.mark.integration
def test_rnaseq_rnaget_expression_ids_view(client):
    r = client.get('/rnaget/expressions')
    assert len(r.json) == 7
    assert r.json[0] == {
        'description': 'All polyA plus RNA-seq samples in humans.',
        'filters': [
            ['file.assay_title', 'polyA plus RNA-seq'],
            ['dataset.replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens']
        ],
        'id': 'EXPID001'
    }


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_formats_view(client):
    r = client.get('/rnaget/expressions/formats')
    assert r.json == ['tsv', 'json']


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_units_view(client):
    r = client.get('/rnaget/expressions/units')
    assert r.json == ['tpm']


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_ticket_view(client):
    r = client.get('/rnaget/expressions/ticket')
    assert r.json == {
        'format': None,
        'units': None,
        'url': 'http://localhost/rnaget/expressions/bytes'
    }
    r = client.get('/rnaget/expressions/ticket?format=tsv')
    assert r.json == {
        'format': 'tsv',
        'units': None,
        'url': 'http://localhost/rnaget/expressions/bytes?format=tsv'
    }
    r = client.get('/rnaget/expressions/ticket?format=tsv&units=tpm')
    assert r.json == {
        'format': 'tsv',
        'units': 'tpm',
        'url': 'http://localhost/rnaget/expressions/bytes?format=tsv&units=tpm'
    }
    r = client.get(
        '/rnaget/expressions/ticket?format=tsv&units=tpm'
        '&assay_title=Total RNA-seq&expression.tpm=gt:45'
        '&sampleIDList=ENCFF1,ENCFF2&featureIDList=ENSG1,ENSG2'
        '&featureNameList=GATA1,POMC,CTCF'
    )
    assert r.json == {
        'format': 'tsv',
        'units': 'tpm',
        'url': (
            'http://localhost/rnaget/expressions/bytes'
            '?format=tsv&units=tpm&assay_title=Total+RNA-seq'
            '&expression.tpm=gt%3A45'
            '&sampleIDList=ENCFF1%2CENCFF2'
            '&featureIDList=ENSG1%2CENSG2'
            '&featureNameList=GATA1%2CPOMC%2CCTCF'
        )
    }


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_ticket_by_expression_id_view(client):
    r = client.get('/rnaget/expressions/EXPID001/ticket')
    assert r.json == {
        'format': None,
        'units': None,
        'url': 'http://localhost/rnaget/expressions/bytes?expressionID=EXPID001'
    }


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_ticket_by_expression_id_view_raise_400(client):
    r = client.get('/rnaget/expressions/NOTEXPID001/ticket')
    assert r.status_code == 400


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_bytes_view_raise_400_when_filter_not_specified(client):
    r = client.get('/rnaget/expressions/bytes?format=tsv')
    assert r.status_code == 400
    assert r.json['message'] == '400 Bad Request: Must filter by feature (gene) or sample property'


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_bytes_view_raise_400_when_format_not_specified(client):
    r = client.get('/rnaget/expressions/bytes')
    assert r.status_code == 400
    assert r.json['message'] == '400 Bad Request: Must specify format'


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_bytes_tsv_view(client, rnaseq_data_in_elasticsearch):
    from io import StringIO
    import csv
    r = client.get(
        '/rnaget/expressions/bytes?format=tsv'
        '&sampleIDList=/files/ENCFF106SZG/,/files/ENCFF241WYH/,'
        '/files/ENCFF273KTX/,/files/ENCFF730OTJ/'
    )
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
    r = client.get(
        '/rnaget/expressions/bytes?format=tsv&featureNameList=RNF19A'
    )
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
        ['ENSG00000034677.12', 'RNF19A', '9.34', '9.34', '9.34', '9.34']
    ]
    assert actual == expected
    r = client.get(
        (
            '/rnaget/expressions/bytes?format=tsv'
            '&featureNameList=RNF19A'
            '&sampleIDList=/files/ENCFF106SZG/,/files/ENCFF241WYH/'
        )
    )
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
        ],
        ['ENSG00000034677.12', 'RNF19A', '9.34', '9.34']
    ]
    assert actual == expected
    r = client.get(
        (
            '/rnaget/expressions/bytes?format=tsv'
            '&featureNameList=RNF19A'
            '&sampleIDList=/files/ENCFF106SZG/,/files/ENCFF241WYH/'
            '&dataset.biosample_summary=muscle of trunk tissue female embryo (113 days)'
        )
    )
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
            '/files/ENCFF241WYH/, muscle of trunk tissue female embryo (113 days)',
        ],
        ['ENSG00000034677.12', 'RNF19A', '9.34']
    ]
    assert actual == expected


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_bytes_json_view(client, rnaseq_data_in_elasticsearch):
    from io import StringIO
    import csv
    r = client.get(
        '/rnaget/expressions/bytes?format=json'
    )
    assert len(r.json['@graph']) == 16
    r = client.get(
        (
            '/rnaget/expressions/bytes?format=json'
            '&featureNameList=RNF19A'
            '&sampleIDList=/files/ENCFF106SZG/,/files/ENCFF241WYH/'
        ),
        follow_redirects=True
    )
    assert len(r.json['@graph']) == 2


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_id_bytes_view_raise_400_when_format_not_specified(client):
    r = client.get('/rnaget/expressions/EXPID001/bytes')
    assert r.status_code == 400
    assert r.json['message'] == '400 Bad Request: Must specify format'


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_id_bytes_view_raise_400_when_expression_id_does_not_exist(client):
    r = client.get('/rnaget/expressions/NOTEXPID001/bytes?format=tsv')
    assert r.status_code == 400
    assert r.json['message'] == '400 Bad Request: Invalid ID supplied'


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_id_bytes_tsv_view(client, rnaseq_data_in_elasticsearch):
    from io import StringIO
    import csv
    r = client.get(
        '/rnaget/expressions/EXPID002/bytes?format=tsv&searchTerm=(GM23338|tissue)'
    )
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
            '/files/ENCFF273KTX/, uterus tissue female adult (53 years)',
            '/files/ENCFF730OTJ/, GM23338 originated from GM23248'
        ],
        ['ENSG00000039987.6', '', '0.01', '0.01', '0.01'],
        ['ENSG00000055732.12', '', '0.27', '0.27', '0.27'],
        ['ENSG00000060982.14', '', '10.18', '10.18', '10.18'],
        ['ENSG00000034677.12', 'RNF19A', '9.34', '9.34', '9.34']
    ]
    assert actual == expected
    r = client.get(
        '/rnaget/expressions/EXPID001/bytes?format=tsv&file.@id=*'
    )
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
            '/files/ENCFF241WYH/, muscle of trunk tissue female embryo (113 days)',
        ],
        ['ENSG00000039987.6', '', '0.01'],
        ['ENSG00000055732.12', '', '0.27'],
        ['ENSG00000060982.14', '', '10.18'],
        ['ENSG00000034677.12', 'RNF19A', '9.34']
    ]
    assert actual == expected


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_id_bytes_json_view(client, rnaseq_data_in_elasticsearch):
    r = client.get(
        '/rnaget/expressions/EXPID001/bytes?format=json'
    )
    assert len(r.json['@graph']) == 4
    r = client.get(
        '/rnaget/expressions/EXPID001/bytes?format=json&studyID=ENCSR906HEV'
    )
    assert len(r.json['@graph']) == 4
    assert r.json['@graph'][0]['dataset']['@id'] == '/experiments/ENCSR906HEV/'


@pytest.mark.integration
def test_rnaseq_rnaget_expressions_filters_view(client, rnaseq_data_in_elasticsearch):
    r = client.get('/rnaget/expressions/filters')
    assert r.status_code == 200
    assert len(r.json) == 7
    assert r.json == [
        {
            'description': 'Data Type',
            'filter': 'type',
            'values': ['RNAExpression']
        },
        {
            'description': 'Assay title',
            'filter': 'file.assay_title',
            'values': [
                'total RNA-seq',
                'polyA plus RNA-seq'
            ]
        },
        {
            'description': 'Biosample classification',
            'filter': 'file.biosample_ontology.classification',
            'values': [
                'cell line',
                'tissue'
            ]
        },
        {
            'description': 'Biosample term name',
            'filter': 'file.biosample_ontology.term_name',
            'values': [
                'GM23338',
                'muscle of trunk',
                'uterus'
            ]
        },
        {
            'description': 'Assembly',
            'filter': 'file.assembly',
            'values': [
                'GRCh38'
            ]
        },
        {
            'description': 'Organism',
            'filter': 'dataset.replicates.library.biosample.donor.organism.scientific_name',
            'values': [
                'Homo sapiens'
            ]
        },
        {
            'description': 'Biosample sex',
            'filter': 'dataset.replicates.library.biosample.sex',
            'values': [
                'female',
                'male'
            ]
        }
    ]


@pytest.mark.integration
def test_rnaseq_rnaget_service_info(client):
    r = client.get('/rnaget/service-info')
    assert r.json == {
        'contactUrl': 'mailto:encode-help@lists.stanford.edu',
        'description': 'This service implements the GA4GH RNAget API for ENCODE data',
        'id': 'org.ga4gh.encodeproject',
        'name': 'ENCODE RNAget',
        'organization': {
            'name': 'ENCODE',
            'url': 'https://www.encodeproject.org'
        },
        'supported': {
            'continuous': False,
            'expressions': True,
            'projects': True,
            'studies': True
        },
        'type': {
            'artifact': 'rnaget',
            'group': 'org.encodeproject',
            'version': '1.1.0'
        },
        'version': '0.0.2'
    }


@pytest.mark.integration
def test_rnaseq_rnaget_continuous_not_implemented(client):
    r = client.get('/rnaget/continuous/ABC/ticket')
    assert r.status_code == 501
    r = client.get('/rnaget/continuous/ABC/bytes')
    assert r.status_code == 501
    r = client.get('/rnaget/continuous/ticket')
    assert r.status_code == 501
    r = client.get('/rnaget/continuous/bytes')
    assert r.status_code == 501
    r = client.get('/rnaget/continuous/formats')
    assert r.status_code == 501
    r = client.get('/rnaget/continuous/filters')
    assert r.status_code == 501
