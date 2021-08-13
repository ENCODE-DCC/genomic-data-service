import pytest
from genomic_data_service import app


def test_searches_adapters_requests_args_adapters_init():
    from genomic_data_service.searches.adapters.requests import ArgsAdapter
    from werkzeug.datastructures import MultiDict
    aa = ArgsAdapter(MultiDict())
    assert isinstance(aa, ArgsAdapter)


def test_searches_adapters_requests_args_adapters_items():
    from genomic_data_service.searches.adapters.requests import ArgsAdapter
    from werkzeug.datastructures import MultiDict
    aa = ArgsAdapter(MultiDict([('a', 'b'), ('a', 'c')]))
    assert list(aa.items()) == [('a', 'b'), ('a', 'c')]


def test_requests_from_app():
    with app.test_client() as client:
        print(client)
        assert False


def test_requests_from_app():
    with app.test_client() as client:
        print(client)
        assert False
