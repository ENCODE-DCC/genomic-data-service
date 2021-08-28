from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request as current_request

from genomic_data_service.rnaseq.remote.portal import get_json
from genomic_data_service.rnaseq.rnaget.constants import BASE_SEARCH_URL
from genomic_data_service.rnaseq.rnaget.constants import DATASET_FILTERS
from genomic_data_service.rnaseq.rnaget.constants import EXPRESSION_IDS
from genomic_data_service.rnaseq.rnaget.constants import PROJECTS
from genomic_data_service.rnaseq.rnaget.constants import TICKET_PATH
from genomic_data_service.rnaseq.rnaget.mapping import convert_facet_to_filter
from genomic_data_service.rnaseq.rnaget.mapping import convert_study_fields
from genomic_data_service.rnaseq.rnaget.mapping import map_fields
from genomic_data_service.searches.requests import make_search_request

from snosearch.parsers import QueryString


rnaget_api = Blueprint(
    'rnaget_api',
    __name__,
)


@rnaget_api.route('/projects', methods=['GET'])
def projects():
    return jsonify(PROJECTS)


@rnaget_api.route('/projects/<project_id>', methods=['GET'])
def project_id(project_id):
    projects = [
        project
        for project in PROJECTS
        if project['id'] == project_id
    ]
    if not projects:
        abort(404, 'Project not found')
    return jsonify(projects)


@rnaget_api.route('/projects/filters', methods=['GET'])
def project_filters():
    return jsonify([])


def get_studies(filters=None):
    filters = filters or []
    qs = QueryString(
        make_search_request()
    )
    qs.extend(
        DATASET_FILTERS + filters
    )
    url = (
        f'{BASE_SEARCH_URL}'
        f'?{qs.get_query_string()}'
    )
    return get_json(url)


@rnaget_api.route('/studies', methods=['GET'])
def studies():
    studies = [
        convert_study_fields(study)
        for study in get_studies()['@graph']
    ]
    return jsonify(studies)


@rnaget_api.route('/studies/<study_id>', methods=['GET'])
def studies_id(study_id):
    filters = [
        ('accession', study_id),
    ]
    studies = [
        convert_study_fields(study)
        for study in get_studies(filters=filters)['@graph']
    ]
    if not studies:
        abort(404, 'Study not found')
    return jsonify(studies)


@rnaget_api.route('/studies/filters', methods=['GET'])
def study_filters():
    filters = [
        convert_facet_to_filter(facet)
        for facet in get_studies()['facets']
    ]
    return jsonify(filters)


@rnaget_api.route('/expressions', methods=['GET'])
def expression_ids():
    return jsonify(EXPRESSION_IDS)


@rnaget_api.route('/expressions/formats', methods=['GET'])
def expressions_formats():
    formats = ['tsv', 'json']
    return jsonify(formats)


@rnaget_api.route('/expressions/units', methods=['GET'])
def expressions_units():
    units = ['tpm']
    return jsonify(units)


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


def expressions_matrix():
    pass


def expressions_report():
    pass


def expressions_factory():
    format_ = get_format_or_raise_400()
    if format_ == 'tsv':
        return expressions_matrix()
    return expression_report()


def parse_expression_filters():
    return []


@rnaget_api.route('/expressions/bytes', methods=['GET'])
def expressions_bytes():
    expressions = expressions_factory()
    return expressions


def get_ticket_url(query_string):
    path = (
        f'{current_request.host_url}'
        f'{TICKET_PATH}'
    )
    if query_string:
        path += f'?{query_string}'
    return path


def make_expression_ticket():
    qs = QueryString(
        make_search_request()
    )
    query_string = qs.get_query_string()
    return {
        'format': get_format(),
        'units': get_unit(),
        'url': get_ticket_url(query_string),
    }


@rnaget_api.route('/expressions/ticket', methods=['GET'])
def expressions_ticket():
    return make_expression_ticket()


@rnaget_api.route('/expressions/<expression_id>/ticket', methods=['GET'])
def expressions_id_ticket(expression_id):
    return {}


@rnaget_api.route('/expressions/<expression_id>/bytes', methods=['GET'])
def expressions_id_bytes(expression_id):
    return []


@rnaget_api.route('/expressions/filters', methods=['GET'])
def expressions_filters():
    return jsonify([])


@rnaget_api.route('/service-info', methods=['GET'])
def service_info():
    info = {
        'id': 'org.ga4gh.encodeproject',
        'name': 'ENCODE RNAget',
        'type': {
            'group': 'org.encodeproject',
            'artifact': 'rnaget',
            'version': '1.2.0'
        },
        'description': 'This service implements the GA4GH RNAget API for ENCODE data',
        'organization': {
            'name': 'ENCODE',
            'url': 'https://www.encodeproject.org'
        },
        'contactUrl': 'mailto:encode-help@lists.stanford.edu',
        'version': '0.0.2',
        'supported': {
            'projects': True,
            'studies': True,
            'expressions': True,
            'continuous': False
        }
    }
    return jsonify(info)


@rnaget_api.route('/continuous/<continuous_id>/ticket', methods=['GET'])
def continuous_id_ticket(continuous_id):
    return abort(501)


@rnaget_api.route('/continuous/<continuous_id>/bytes', methods=['GET'])
def continuous_id_bytes(continuous_id):
    return abort(501)


@rnaget_api.route('/continuous/ticket', methods=['GET'])
def continuous_ticket():
    return abort(501)


@rnaget_api.route('/continuous/bytes', methods=['GET'])
def continuous_bytes():
    return abort(501)


@rnaget_api.route('/continuous/formats', methods=['GET'])
def continuous_formats():
    return abort(501)


@rnaget_api.route('/continuous/filters', methods=['GET'])
def continuous_filters():
    return abort(501)
