import pytest


@pytest.fixture
def client():
    from genomic_data_service import app
    app.config['DEBUG'] = True
    with app.test_client() as client:
        yield client


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
