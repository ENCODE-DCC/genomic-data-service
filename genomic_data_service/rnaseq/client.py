from elasticsearch import Elasticsearch


def add_rna_client(app):
    host = app.config.get("RNA_GET_ES")
    es = Elasticsearch(
        host,
        timeout=30,
    )
    app.registry["RNA_CLIENT"] = es
