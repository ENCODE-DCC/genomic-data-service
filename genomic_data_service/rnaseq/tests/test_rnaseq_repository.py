import pytest

def test_rnaseq_repository_memory_init():
    from genomic_data_service.rnaseq.repository.memory import Memory
    memory = Memory()
    assert isinstance(memory, Memory)


def test_rnaseq_repository_memory_load(as_expressions):
    from genomic_data_service.rnaseq.repository.memory import Memory
    memory = Memory()
    memory.load(as_expressions[1])
    assert len(memory._data) == 1


def test_rnaseq_repository_memory_bulk_load(as_expressions):
    from genomic_data_service.rnaseq.repository.memory import Memory
    memory = Memory()
    memory.bulk_load(as_expressions)
    assert len(memory._data) == 3


def test_rnaseq_repository_elasticsearch_init():
    from genomic_data_service.rnaseq.repository.elasticsearch import ElasticsSearch
    es = ElasticsSearch()
    assert isinstance(es, ElasticsSearch)


def test_rnaseq_repository_elasticsearch_load():
    from genomic_data_service.rnaseq.repository.elasticsearch import ElasticsSearch
    es = ElasticsSearch()
    es.load({})
    assert False


def test_rnaseq_repository_elasticsearch_bulk_load():
    from genomic_data_service.rnaseq.repository.elasticsearch import ElasticsSearch
    es = ElasticsSearch()
    es.bulk_load([])
    assert False
