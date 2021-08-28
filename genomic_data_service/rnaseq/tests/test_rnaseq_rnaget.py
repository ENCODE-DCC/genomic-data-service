import pytest


@pytest.fixture
def client():
    from genomic_data_service import app
    app.config['DEBUG'] = True
    with app.test_client() as client:
        yield client


def test_rnaseq_rnaget_map_field():
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
    assert '@id' not in r.json[0]
    assert 'accession' in r.json[0]
    r = client.get('/rnaget/studies?limit=1&field=description')
    assert len(r.json) == 1
    assert 'id' in r.json[0]
    assert 'accession' not in r.json[0]
    assert 'description' in r.json[0]
