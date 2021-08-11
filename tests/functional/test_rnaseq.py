from genomic_data_service.models import Study, Project, Expression, File


def test_study_filters(test_client):
    response = test_client.get('/studies/filters')
    assert response.status_code == 200
    assert response.json == Study.FILTERS


def test_project_filters(test_client):
    response = test_client.get('/projects/filters')
    assert response.status_code == 200
    assert response.json == Project.FILTERS


def test_expression_filters(test_client):
    response = test_client.get('/expressions/filters')
    assert response.status_code == 200
    assert response.json == Expression.FILTERS


def test_expression_format_accepts_tsv_only(test_client):
    response = test_client.get('/expressions/formats')
    assert response.status_code == 200
    assert response.json == ['tsv', 'json']


def test_continuous_endpoints_should_return_501(test_client):
    endpoints = ['random_id/ticket', 'random_id/bytes', 'ticket', 'bytes', 'formats', 'filters']

    for endpoint in endpoints:
        response = test_client.get('/continuous/' + endpoint)
        assert response.status_code == 501


def test_service_info(test_client):
    response = test_client.get('/service-info')
    assert response.status_code == 200

    keys = ['contactUrl', 'createdAt', 'description', 'documentationUrl', 'environment', 'id', 'name', 'organization', 'supported', 'type', 'updatedAt', 'version']
    for key in keys:
        assert key in response.json

    assert response.json['supported']['continuous'] == False
    assert response.json['supported']['expressions'] == True
    assert response.json['supported']['projects'] == True
    assert response.json['supported']['studies'] == True
