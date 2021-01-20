from flask import Flask
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

    # Enabled endpoints:
    import genomic_data_service.search
    import genomic_data_service.summary
    import genomic_data_service.rna_seq

    @app.route('/healthcheck/', methods=['GET'])
    def healthcheck():
        es.cluster.health()
        return 'ok'
