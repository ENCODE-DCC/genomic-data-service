from flask import jsonify
from genomic_data_service import app


@app.errorhandler(400)
def invalid_request(e):
    return jsonify(message=str(e)), 400


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(message=str(e)), 404


@app.errorhandler(501)
def resource_not_found(e):
    return jsonify(message=str(e)), 501
