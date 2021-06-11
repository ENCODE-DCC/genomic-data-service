from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ

def is_web_app():
    return ('FLASK_APP' in environ)

app = Flask(__name__)

if 'GENOMIC_DATA_SERVICE_SETTINGS' in environ:
    app.config.from_envvar('GENOMIC_DATA_SERVICE_SETTINGS')
else:
    print('[CONFIG] Defaulting to development config')
    app.config.from_pyfile('../config/development.cfg')


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
