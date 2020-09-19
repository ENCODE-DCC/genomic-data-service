def test_from_parameter_is_invalid(test_client):
    response = test_client.get('/regulome-search?from=10')
    assert response.status_code == 400
    assert b"Invalid parameters" in response.data

def test_size_parameter_is_invalid(test_client):
    response = test_client.get('/regulome-search?size=10')
    assert response.status_code == 400
    assert b"Invalid parameters" in response.data
