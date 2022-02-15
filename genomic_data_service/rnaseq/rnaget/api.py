from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request as current_request

from genomic_data_service.rnaseq.rnaget.constants import EXPRESSION_IDS
from genomic_data_service.rnaseq.rnaget.constants import PROJECTS
from genomic_data_service.rnaseq.rnaget.constants import SERVICE_INFO
from genomic_data_service.rnaseq.rnaget.mapping import convert_facet_to_filter
from genomic_data_service.rnaseq.rnaget.mapping import convert_study_fields
from genomic_data_service.rnaseq.rnaget.mapping import map_fields
from genomic_data_service.rnaseq.rnaget.expressions import expressions_factory
from genomic_data_service.rnaseq.rnaget.expressions import get_format
from genomic_data_service.rnaseq.rnaget.expressions import get_format_or_raise_400
from genomic_data_service.rnaseq.rnaget.expressions import get_ticket_url
from genomic_data_service.rnaseq.rnaget.expressions import get_expressions
from genomic_data_service.rnaseq.rnaget.expressions import make_expression_ticket
from genomic_data_service.rnaseq.rnaget.expressions import (
    make_rnaget_expressions_search_request,
)
from genomic_data_service.rnaseq.rnaget.expressions import (
    validate_expression_id_or_raise_400,
)
from genomic_data_service.rnaseq.rnaget.studies import get_studies
from genomic_data_service.searches.requests import make_search_request

from snosearch.parsers import QueryString


rnaget_api = Blueprint(
    "rnaget_api",
    __name__,
)


@rnaget_api.route("/projects", methods=["GET"])
def projects():
    return jsonify(PROJECTS)


@rnaget_api.route("/projects/<project_id>", methods=["GET"])
def project_id(project_id):
    projects = [project for project in PROJECTS if project["id"] == project_id]
    if not projects:
        abort(404, "Project not found")
    return jsonify(projects)


@rnaget_api.route("/projects/filters", methods=["GET"])
def project_filters():
    return jsonify([])


@rnaget_api.route("/studies", methods=["GET"])
def studies():
    studies = [convert_study_fields(study) for study in get_studies()["@graph"]]
    return jsonify(studies)


@rnaget_api.route("/studies/<study_id>", methods=["GET"])
def studies_id(study_id):
    filters = [
        ("accession", study_id),
    ]
    studies = [
        convert_study_fields(study) for study in get_studies(filters=filters)["@graph"]
    ]
    if not studies:
        abort(404, "Study not found")
    return jsonify(studies)


@rnaget_api.route("/studies/filters", methods=["GET"])
def study_filters():
    filters = [convert_facet_to_filter(facet) for facet in get_studies()["facets"]]
    return jsonify(filters)


@rnaget_api.route("/expressions", methods=["GET"])
def expression_ids():
    return jsonify(EXPRESSION_IDS)


@rnaget_api.route("/expressions/formats", methods=["GET"])
def expressions_formats():
    formats = ["tsv", "json"]
    return jsonify(formats)


@rnaget_api.route("/expressions/units", methods=["GET"])
def expressions_units():
    units = ["tpm", "fpkm"]
    return jsonify(units)


@rnaget_api.route("/expressions/ticket", methods=["GET"])
def expressions_ticket():
    qs = QueryString(make_search_request())
    return make_expression_ticket(qs.get_query_string())


@rnaget_api.route("/expressions/<expression_id>/ticket", methods=["GET"])
def expressions_id_ticket(expression_id):
    validate_expression_id_or_raise_400(expression_id)
    qs = QueryString(make_search_request())
    qs.append(("expressionID", expression_id))
    return make_expression_ticket(qs.get_query_string())


@rnaget_api.route("/expressions/bytes", methods=["GET"])
def expressions_bytes():
    search_request = make_rnaget_expressions_search_request()
    expressions = expressions_factory()
    return expressions(search_request)


@rnaget_api.route("/expressions/<expression_id>/bytes", methods=["GET"])
def expressions_id_bytes(expression_id):
    validate_expression_id_or_raise_400(expression_id)
    filters = [
        ("expressionID", expression_id),
    ]
    search_request = make_rnaget_expressions_search_request(filters=filters)
    expressions = expressions_factory()
    return expressions(search_request)


@rnaget_api.route("/expressions/filters", methods=["GET"])
def expressions_filters():
    filters = [
        convert_facet_to_filter(facet) for facet in get_expressions().json["facets"]
    ]
    return jsonify(filters)


@rnaget_api.route("/service-info", methods=["GET"])
def service_info():
    return jsonify(SERVICE_INFO)


@rnaget_api.route("/continuous/<continuous_id>/ticket", methods=["GET"])
def continuous_id_ticket(continuous_id):
    return abort(501)


@rnaget_api.route("/continuous/<continuous_id>/bytes", methods=["GET"])
def continuous_id_bytes(continuous_id):
    return abort(501)


@rnaget_api.route("/continuous/ticket", methods=["GET"])
def continuous_ticket():
    return abort(501)


@rnaget_api.route("/continuous/bytes", methods=["GET"])
def continuous_bytes():
    return abort(501)


@rnaget_api.route("/continuous/formats", methods=["GET"])
def continuous_formats():
    return abort(501)


@rnaget_api.route("/continuous/filters", methods=["GET"])
def continuous_filters():
    return abort(501)
