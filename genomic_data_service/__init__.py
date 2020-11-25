from flask import Flask
from os import environ

app = Flask(__name__)

if 'GENOMIC_DATA_SERVICE_SETTINGS' in environ:
    app.config.from_envvar('GENOMIC_DATA_SERVICE_SETTINGS')
else:
    print('[CONFIG] Defaulting to development config')
    app.config.from_pyfile('../config/development.cfg')


if 'FLASK_APP' in environ:
    from elasticsearch import Elasticsearch
    
    es = Elasticsearch(port=app.config['ES_PORT'], hosts=app.config['ES_HOSTS'])

    # Enabled endpoints:
    import genomic_data_service.search
    import genomic_data_service.summary

    @app.route('/healthcheck/', methods=['GET'])
    def healthcheck():
        return 'ok'
