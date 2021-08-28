from flask import abort
from flask import Blueprint
from flask import jsonify

from genomic_data_service.rnaseq.remote.portal import get_json
from genomic_data_service.rnaseq.rnaget.constants import BASE_SEARCH_URL
from genomic_data_service.rnaseq.rnaget.constants import DATASET_FILTERS
from genomic_data_service.rnaseq.rnaget.constants import DATASET_FROM_TO_FIELD_MAP
from genomic_data_service.rnaseq.rnaget.constants import PROJECTS
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


@rnaget_api.route('/studies', methods=['GET'])
def studies():
    qs = QueryString(make_search_request())
    qs.extend(DATASET_FILTERS)
    url = f'{BASE_SEARCH_URL}?{qs.get_query_string()}'
    results = [
        map_fields(item, DATASET_FROM_TO_FIELD_MAP)
        for item in get_json(url)['@graph']
    ]
    return jsonify(results)
