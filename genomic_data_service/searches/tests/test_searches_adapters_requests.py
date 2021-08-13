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


def test_searches_adapters_requests_request_adapter_init():
    from genomic_data_service.searches.adapters.requests import RequestAdapter
    from flask import Request
    request = Request({})
    ra = RequestAdapter(request)
    assert isinstance(ra, RequestAdapter)


def test_searches_adapters_requests_request_adapter_params():
    from genomic_data_service.searches.adapters.requests import RequestAdapter
    from flask import Request
    request = Request(
        {
            'QUERY_STRING':
            'type=Experiment&type=RNAExpression&field=status&files.file_type=bed+bed3%2B'
            '&accession!=ABC'
        }
    )
    ra = RequestAdapter(request)
    assert list(ra.params.items()) == [
        ('type', 'Experiment'),
        ('type', 'RNAExpression'),
        ('field', 'status'),
        ('files.file_type', 'bed bed3+'),
        ('accession!', 'ABC')
    ]
