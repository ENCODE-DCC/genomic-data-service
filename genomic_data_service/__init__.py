from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ

from genomic_data_service.searches.configs import add_registry
from genomic_data_service.rnaseq.client import add_rna_client
from genomic_data_service.rnaseq.rnaget import rnaget_api


def is_web_app():
    return ('FLASK_APP' in environ)

app = Flask(__name__)
app.register_blueprint(rnaget_api, url_prefix='/rnaget/')


if 'GENOMIC_DATA_SERVICE_SETTINGS' in environ:
    app.config.from_envvar('GENOMIC_DATA_SERVICE_SETTINGS')
else:
    print('[CONFIG] Defaulting to development config')
    app.config.from_pyfile('../config/development.cfg')

add_registry(app)
add_rna_client(app)

if is_web_app:
    from elasticsearch import Elasticsearch
    
    es = Elasticsearch(port=app.config['ES_PORT'], hosts=app.config['ES_HOSTS'])

    regulome_es = Elasticsearch(port=app.config['REGULOME_ES_PORT'], hosts=app.config['REGULOME_ES_HOSTS'])
    region_search_es = Elasticsearch(port=app.config['REGION_SEARCH_ES_PORT'], hosts=app.config['REGION_SEARCH_ES_HOSTS'])

    db = SQLAlchemy(app)

    app.url_map.strict_slashes = False

    import genomic_data_service.models

    # Enabled endpoints:
    import genomic_data_service.search
    import genomic_data_service.summary
    import genomic_data_service.rna_seq
    
    @app.route('/healthcheck/', methods=['GET'])
    def healthcheck():
        es.cluster.health()
        return 'ok'

import genomic_data_service.rnaseq.views
