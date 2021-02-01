from genomic_data_service import es, app
from flask import jsonify, abort, request, send_file, redirect
import flask_excel as excel
from .models import Project, Study, File, Expression

import os.path
from os import path

ACCEPTED_FORMATS = ['tsv']

excel.init_excel(app)

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


@app.route('/expressions/filters', methods=['GET'])
def expressions_filters():
    return jsonify(Expression.FILTERS)


@app.route('/expressions/formats', methods=['GET'])
def expressions_formats():
    return jsonify(ACCEPTED_FORMATS)


def get_custom_expression_matrix_from_file(expression_id, request, return_raw_content=False):
    # considering features to be genes for now
    gene_names = request.args.get('featureNameList')
    gene_ids = request.args.get('featureIDList')
    sample_ids = request.args.get('sampleIDList')

    file = File.query.filter_by(id=expression_id)

    if sample_ids:
        sample_ids = sample_ids.split(",")

        file = file.filter(File.study_id.in_(sample_ids)).first_or_404(description="Expression not found")
    else:
        file = file.first_or_404(description="Expression not found")

    if gene_names or gene_ids:
        if gene_names:
            gene_names = gene_names.split(",")
        if gene_ids:
            gene_ids = gene_ids.split(",")

        if return_raw_content:
            content = file.expressions_with_feature_list(gene_names, gene_ids)

            file_name = expression_id + "_custom_expressions." + file.file_type
            return excel.make_response_from_array(content, file.file_type, file_name=file_name)
        else:
            return file.generate_file_from_feature_list(gene_names, gene_ids, app.config['MATRIX_FILE_PATH'], request.host)
    else:
        if return_raw_content:
            return redirect(file.url)
        else:
            return file.to_dict()


@app.route('/expressions/<expression_id>/ticket', methods=['GET'])
def expressions_id_ticket(expression_id):
    response = get_custom_expression_matrix_from_file(expression_id, request)
    response['headers'] = {} # no headers for now

    return jsonify(response)


@app.route('/expressions/<expression_id>/bytes', methods=['GET'])
def expressions_id_bytes(expression_id):
    return get_custom_expression_matrix_from_file(expression_id, request, return_raw_content=True)


@app.route('/download/<file_path>', methods=['GET'])
def download_file_path(file_path):
    system_file_path = app.config['MATRIX_FILE_PATH'] + file_path

    if path.exists(system_file_path): # TODO: replace this by Redis lookup
        return send_file(system_file_path, as_attachment=True)

    abort(404, description="File not found")


