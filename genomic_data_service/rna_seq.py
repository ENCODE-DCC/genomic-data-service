from genomic_data_service import app
from flask import jsonify, abort, request, send_file, redirect
import flask_excel as excel
from genomic_data_service.models import Project, Study, File, Expression
from genomic_data_service.expression_service import ExpressionService

import os.path
from os import path

excel.init_excel(app)

@app.errorhandler(400)
def invalid_request(e):
    return jsonify(message=str(e)), 400


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(message=str(e)), 404


@app.route('/projects', methods=['GET'])
def projects():
    version = request.args.get('version')
    if version:
        return jsonify([project.to_dict() for project in Project.query.filter_by(version=version)])

    return jsonify([project.to_dict() for project in Project.query.all()])


@app.route('/projects/<project_id>', methods=['GET'])
def project_id(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404(description="Project not found")

    return jsonify(project.to_dict())


@app.route('/projects/filters', methods=['GET'])
def project_filters():
    return jsonify(Project.FILTERS)


@app.route('/studies', methods=['GET'])
def studies():
    version = request.args.get('version')
    if version:
        return jsonify([study.to_dict() for study in Study.query.filter_by(version=version)])

    return jsonify([study.to_dict() for study in Study.query.all()])


@app.route('/studies/<study_id>', methods=['GET'])
def studies_id(study_id):
    study = Study.query.filter_by(id=study_id).first_or_404(description="Study not found")

    return jsonify(study.to_dict())


@app.route('/studies/filters', methods=['GET'])
def study_filters():
    return jsonify(Study.FILTERS)


@app.route('/download/<file_path>', methods=['GET'])
def download_file_path(file_path):
    system_file_path = app.config['MATRIX_FILE_PATH'] + file_path

    if path.exists(system_file_path): # TODO: replace this by Redis lookup
        return send_file(system_file_path, as_attachment=True)

    abort(404, description="File not found")


@app.route('/expressions/filters', methods=['GET'])
def expressions_filters():
    return jsonify(Expression.FILTERS)


@app.route('/expressions/formats', methods=['GET'])
def expressions_formats():
    return jsonify(File.ACCEPTED_FORMATS)


def extract_expression_params(request, params_list=None, expression_id=None):
    params = params_list or ['format', 'projectID', 'studyID', 'version', 'sampleIDList', 'featureIDList', 'featureNameList']
    params_dict = {}
    for param in params:
        params_dict[param] = request.args.get(param)

    if expression_id:
        params_dict['expression_id'] = expression_id

    return params_dict


@app.route('/expressions/ticket', methods=['GET'])
def expressions_ticket():
    service = ExpressionService(extract_expression_params(request))

    if service.unacceptable_format():
        return abort(400, description="Format not present or not accepted. Current available formats: " + ", ".join(File.ACCEPTED_FORMATS))

    return jsonify(service.get_file_ticket(app.config['MATRIX_FILE_PATH'], request.host + '/download/'))


@app.route('/expressions/bytes', methods=['GET'])
def expressions_bytes():
    service = ExpressionService(extract_expression_params(request))

    if service.unacceptable_format():
        return abort(400, description="Format not present or not accepted. Current available formats: " + ", ".join(File.ACCEPTED_FORMATS))

    file_name = "Expressions." + service.file_type
    return excel.make_response_from_array(service.get_expressions(), service.file_type, file_name=file_name)


@app.route('/expressions/<expression_id>/ticket', methods=['GET'])
def expressions_id_ticket(expression_id):
    params = extract_expression_params(request, params_list=['featureIDList', 'featureNameList'], expression_id=expression_id)
    service = ExpressionService(params)

    if not service.valid_expression_id():
        return abort(404, description="Expression ID not found")

    return jsonify(service.get_file_ticket(app.config['MATRIX_FILE_PATH'], request.host + '/download/'))


@app.route('/expressions/<expression_id>/bytes', methods=['GET'])
def expressions_id_bytes(expression_id):
    params = extract_expression_params(request, params_list=['featureIDList', 'featureNameList'], expression_id=expression_id)
    service = ExpressionService(params)

    if not service.valid_expression_id():
        return abort(404, description="Expression ID not found")

    file_name = "Expressions." + service.file_type
    return excel.make_response_from_array(service.get_expressions(), service.file_type, file_name=file_name)


@app.route('/service-info', methods=['GET'])
def service_info():
    info = {
        'id': 'org.ga4gh.encodeproject',
        'name': 'ENCODE',
        'type': {
            'group': 'org.encodeproject',
            'artifact': 'rnaget',
            'version': '0.0.1'
        },
        'description': 'This service provides and implementation of GA4GH RNA-Get API for ENCODE data',
        'organization': {
            'name': 'the ENCODE Consortium',
            'url': 'https://encodeproject.org'
        },
        'contactUrl': 'mailto:encode-help@lists.stanford.edu',
        'documentationUrl': 'https://dataservices.encodeproject.org',
        'createdAt': '2019-06-04T12:58:19Z',
        'updatedAt': '2019-06-04T12:58:19Z',
        'environment': 'test',
        'version': '1.0.0',
        'supported': {
            'projects': True,
            'studies': True,
            'expressions': True,
            'continuous': False
        }
    }

    return jsonify(info)


# Explicit unsupported endpoints
@app.route('/continuous/<continuous_id>/ticket', methods=['GET'])
def continuous_id_ticket(continuous_id):
    return abort(501)


@app.route('/continuous/<continuous_id>/bytes', methods=['GET'])
def continuous_id_bytes(continuous_id):
    return abort(501)


@app.route('/continuous/ticket', methods=['GET'])
def continuous_ticket():
    return abort(501)


@app.route('/continuous/bytes', methods=['GET'])
def continuous_bytes():
    return abort(501)


@app.route('/continuous/formats', methods=['GET'])
def continuous_formats():
    return abort(501)


@app.route('/continuous/filters', methods=['GET'])
def continuous_filters():
    return abort(501)
