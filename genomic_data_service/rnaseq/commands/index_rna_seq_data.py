from elasticsearch import Elasticsearch as Client

from genomic_data_service.rnaseq.expressions import Expressions
from genomic_data_service.rnaseq.repository.elasticsearch import Elasticsearch
from genomic_data_service.rnaseq.remote.portal import Portal


HOST = '127.0.0.1:9202'


def index_rna_seq_data():
    client = Client([HOST])
    portal = Portal()
    repository = Elasticsearch(client)
    expressions = Expressions(portal, repository)
    expressions.index()


if __name__ == '__main__':
    index_rna_seq_data()
