from elasticsearch import Elasticsearch


def add_rna_client(app):
    host = app.config.get('RNA_GET_ES')
    es = Elasticsearch(
        host,
        timeout=200,
        retry_on_timeout=True,
    )
    app.registry['RNA_CLIENT'] = es
