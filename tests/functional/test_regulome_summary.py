def test_valid_params(test_client):
    response = test_client.get(
        "summary/?regions=rs75982468%0D%0Ars7745856&genome=GRCh37&maf=0.01"
    )
    assert response.status_code == 200


def test_invalid_params_from(test_client):

    response = test_client.get(
        "summary/?regions=rs75982468%0D%0Ars7745856&genome=GRCh37&maf=0.01&from=25"
    )
    assert response.status_code == 400


def test_valid_params_limit_1(test_client):

    response = test_client.get(
        "summary/?regions=rs75982468%0D%0Ars7745856&genome=GRCh37&maf=0.01&limit=1"
    )
    assert response.status_code == 200


def test_valid_params_limit_all(test_client):

    response = test_client.get(
        "summary/?regions=rs75982468%0D%0Ars7745856&genome=GRCh37&maf=0.01&limit=all"
    )
    assert response.status_code == 200


def test_valid_params_limit_exception(test_client):

    response = test_client.get(
        "summary/?regions=rs75982468%0D%0Ars7745856&genome=GRCh37&maf=0.01&limit=no"
    )
    assert response.status_code == 200
