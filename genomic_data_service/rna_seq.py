from genomic_data_service import es, app
from flask import jsonify, abort

ENCODE = {
        "version": "v110.0",
        "description": "ENCODE: Encyclopedia of DNA Elements - https://encodeproject.org",
        "id": "project_1",
        "name": "Encode",
        "tags": {}
    }


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(message=str(e)), 404


@app.route('/projects', methods=['GET'])
def projects():
    return jsonify([ENCODE])


@app.route('/projects/<project_id>', methods=['GET'])
def project_id(project_id):
    if project_id == ENCODE["id"]:
        return jsonify([ENCODE])

    abort(404, "Project not found")

@app.route('/projects/filters', methods=['GET'])
def project_filters():
    return jsonify([])
