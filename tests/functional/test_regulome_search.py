def test_from_parameter_is_invalid(test_client):
    response = test_client.get('search/?from=10')
    assert response.status_code == 400
    assert b'Invalid parameters' in response.data


def test_size_parameter_is_invalid(test_client):
    response = test_client.get('search/?size=10')
    assert response.status_code == 400
    assert b'Invalid parameters' in response.data


def test_invalid_params(test_client):
    response = test_client.get('search/?size=10&from=50')
    assert response.status_code == 400
    assert b'Invalid parameters' in response.data


def test_valid_params(test_client, mocker):
    mocker.patch('genomic_data_service.search.get_sequence', return_value={})
    response = test_client.get(
        'search/?regions=chr1:39492461-39492462&genome=GRCh37')
    assert response.status_code == 200


def test_list_regions(test_client):
    response = test_client.get(
        'search/?regions=chr1:39492461-39492462 chr10:11741180-11741181&genome=GRCh37'
    )
    assert response.status_code == 200


def test_params_size_all(test_client, mocker):
    mocker.patch('genomic_data_service.search.get_sequence', return_value={})
    response = test_client.get(
        'search/?regions=chr10:11741180-11741181&genome=GRCh37&limit=all'
    )
    data = response.json
    assert data['assembly'] == 'GRCh37'
