from flask import Flask
from elasticsearch import Elasticsearch
from os import environ


app = Flask(__name__)

if 'GENOMIC_DATA_SERVICE_SETTINGS' in environ:
    app.config.from_envvar('GENOMIC_DATA_SERVICE_SETTINGS')
else:
    print('[CONFIG] Defaulting to development config')
    app.config.from_pyfile('../config/development.cfg')


es = Elasticsearch(port=app.config['ES_PORT'], hosts=app.config['ES_HOSTS'])


# Enabled endpoints:
import genomic_data_service.search
import genomic_data_service.summary
