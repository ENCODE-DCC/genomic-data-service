import pytest

from genomic_data_service import app

@pytest.fixture(scope='module')
def test_client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client
