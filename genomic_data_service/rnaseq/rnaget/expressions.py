from flask import abort
from flask import request as current_request
from flask import redirect
from flask import url_for

from genomic_data_service.rnaseq.rnaget.constants import TICKET_PATH
from genomic_data_service.searches.requests import make_search_request

from snosearch.parsers import QueryString


def get_format():
    qs = QueryString(
        make_search_request()
    )
    return qs.get_one_value(
        params=qs.get_key_filters(
            key='format'
        )
    )


def get_unit():
    qs = QueryString(
        make_search_request()
    )
    return qs.get_one_value(
        params=qs.get_key_filters(
            key='units'
        )
    )


def get_format_or_raise_400():
    format_ = get_format()
    if not format_:
        abort(400, 'Must specify format')
    return format_


def expressions_matrix(query_string):
    endpoint = url_for('rnaget_expression_matrix_view')
    location = (
        f'{endpoint}'
        f'?{query_string}'
    )
    return redirect(location)


def expressions_report(query_string):
    endpoint = url_for('rnaget_search_quick_view')
    location = (
        f'{endpoint}'
        f'?{query_string}'
    )
    return redirect(location)


def expressions_factory():
    format_ = get_format_or_raise_400()
    if format_ == 'tsv':
        return expressions_matrix
    return expressions_report


def get_ticket_url(query_string):
    path = (
        f'{current_request.host_url}'
        f'{TICKET_PATH}'
    )
    if query_string:
        path += f'?{query_string}'
    return path


def make_expression_ticket(query_string):
    return {
        'format': get_format(),
        'units': get_unit(),
        'url': get_ticket_url(query_string),
    }
