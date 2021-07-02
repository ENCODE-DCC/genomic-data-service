from elasticsearch import Elasticsearch

from genomic_data_service.rnaseq.expressions import Expressions
from genomic_data_service.rnaseq.repository import Elasticsearch as ESRepository
from genomic_data_service.rnaseq.remote.portal import Portal


HOST = '127.0.0.1'
PORT = 9202


def index_rna_seq_data():
    es = Elasticsearch(
        [f'{HOST}:{PORT}']
    )
    portal = Portal()
    repository = ESRepository(es)
    expressions = Expressions(
        portal=portal,
        repository=repository,
    )
    expressions.index()


if __name__ == '__main__':
    index_rna_seq_data()
