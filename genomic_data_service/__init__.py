from flask import Flask
from elasticsearch import Elasticsearch


app = Flask(__name__)
app.config.from_envvar('GENOMIC_DATA_SERVICE_SETTINGS')

es = Elasticsearch(port=app.config['ES_PORT'], hosts=app.config['ES_HOSTS'])


import genomic_data_service.regulome_search
