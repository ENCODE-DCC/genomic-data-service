import pytest

from flask import Request
from genomic_data_service import app
from werkzeug.datastructures import ImmutableOrderedMultiDict
from genomic_data_service.searches.adapters.requests import RequestAdapter


class DummyRequest(RequestAdapter):

    def __init__(self, request):
        self._request = request

    def __setitem__(self, key, value):
        Request.parameter_storage_class = ImmutableOrderedMultiDict
        environ = self._request.environ.copy()
        environ.update({key: value})
        self._request = Request(environ)

    def __getitem__(self, key):
        return self._request.environ[key]

    @property
    def environ(self):
        return self

    @property
    def query_string(self):
        return self._request.query_string.decode('utf-8')

    @query_string.setter
    def query_string(self, value):
        self.__setitem__('QUERY_STRING', value)


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


def test_searches_adapters_request_works_with_params_parsers():
    from genomic_data_service.searches.adapters.requests import RequestAdapter
    from flask import Request
    from snosearch.parsers import ParamsParser
    request = Request(
        {
            'QUERY_STRING': 'type!=Experiment'
        }
    )
    pp = ParamsParser(RequestAdapter(request))
    assert 'type!' in pp._request.params
    assert pp.is_param('type!', 'Experiment')
    assert not pp.is_param('type', 'RNAExpression')
    assert pp.get_filters_by_condition() == [
        ('type!', 'Experiment')
    ]


def test_searches_adapters_request_works_with_params_parser_get_filters_by_condition():
    from genomic_data_service.searches.adapters.requests import RequestAdapter
    from flask import Request
    from snosearch.parsers import ParamsParser
    request = Request(
        {
            'QUERY_STRING': 'type=Experiment&type=File&field=status'
        }
    )
    pp = ParamsParser(RequestAdapter(request))
    assert pp.get_filters_by_condition(
        key_and_value_condition=lambda k, _: k == 'field'
    ) == [
        ('field', 'status')
    ]
    assert pp.get_filters_by_condition(
        key_and_value_condition=lambda k, _: k == 'type'
    ) == [
        ('type', 'Experiment'),
        ('type', 'File')
    ]
    assert pp.get_search_term_filters() == []
    assert pp.get_must_match_filters() == [
        ('type', 'Experiment'),
        ('type', 'File'),
        ('field', 'status')
    ]


def test_searches_adapters_request_adapter_passes_param_parser_unit_tests():
    from genomic_data_service.searches.adapters.requests import RequestAdapter
    from flask import Request
    from snosearch.parsers import ParamsParser
    from snosearch.tests import test_searches_parsers
    tests = {
        k: v
        for k, v in vars(test_searches_parsers).items()
        if k.startswith('test')
    }
    dummy_request = DummyRequest(Request({}))
    for test_name, test in tests.items():
        dummy_request['QUERY_STRING'] = ''
        print(test_name)
        try:
            test(dummy_request)
        except (ModuleNotFoundError):
            print('skipping')
