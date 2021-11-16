from elasticsearch import Elasticsearch


def add_rna_client(app):
    host = 'http://vpc-rna-expression-dro56qntagtgmls6suff2m7nza.us-west-2.es.amazonaws.com:80'
    es = Elasticsearch(
        host,
        timeout=30,
    )
    app.registry['RNA_CLIENT'] = es
