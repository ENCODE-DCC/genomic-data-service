from elasticsearch import Elasticsearch


def add_rna_client(app):
    host = app.config.get('RNA_GET_ES')
    es = Elasticsearch(host)
    app.registry['RNA_CLIENT'] = es
