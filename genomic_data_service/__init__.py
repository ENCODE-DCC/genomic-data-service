from flask import Flask, jsonify, make_response
from os import environ

from genomic_data_service.searches.configs import add_registry
from genomic_data_service.rnaseq.client import add_rna_client
from genomic_data_service.rnaseq.rnaget.api import rnaget_api
import logging


def is_web_app():
    return 'FLASK_APP' in environ


app = Flask(__name__)
app.register_blueprint(rnaget_api)


if 'GENOMIC_DATA_SERVICE_SETTINGS' in environ:
    app.config.from_envvar('GENOMIC_DATA_SERVICE_SETTINGS')
else:
    logging.info('[CONFIG] Defaulting to development config')
    app.config.from_pyfile('../config/development.cfg')

add_registry(app)
add_rna_client(app)


if is_web_app():
    from elasticsearch import Elasticsearch

    regulome_es = Elasticsearch(
        port=app.config['REGULOME_ES_PORT'], hosts=app.config['REGULOME_ES_HOSTS']
    )
    region_search_es = Elasticsearch(
        port=app.config['REGION_SEARCH_ES_PORT'],
        hosts=app.config['REGION_SEARCH_ES_HOSTS'],
    )
    app.url_map.strict_slashes = False

    # Enabled endpoints:
    import genomic_data_service.search
    import genomic_data_service.summary
    import genomic_data_service.rnaseq.views
    import genomic_data_service.errors

    @app.route('/healthcheck/', methods=['GET'])
    def healthcheck():
        status = {}
        try:
            status['regulome_es'] = regulome_es.cluster.health()
            status['region_search_es'] = region_search_es.cluster.health()
        except Exception as e:
            status['exception'] = str(e)

        response_out = make_response(
            jsonify(status),
            200,
        )
        response_out.headers = {'Content-Type': 'application/json'}
        return response_out
