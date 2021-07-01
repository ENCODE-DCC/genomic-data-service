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


def test_rnaseq_repository_memory_bulk_load_from_files(mocker, mock_portal, raw_expressions):
    from genomic_data_service.rnaseq.repository.memory import Memory
    mocker.patch(
        'genomic_data_service.rnaseq.domain.file.get_expression_generator',
        return_value=raw_expressions,
    )
    memory = Memory()
    files = list(mock_portal.get_rna_seq_files())
    assert len(files) == 4
    memory.bulk_load_from_files(files)
    # Four expression values for four files.
    assert len(memory._data) == 16
    assert memory._data[0] == {
        'embedded': {
            'expression': {
                'gene_id': 'ENSG00000034677.12',
                'transcript_ids': [
                    'ENST00000341084.6',
                    'ENST00000432381.2',
                    'ENST00000517584.5',
                    'ENST00000519342.1',
                    'ENST00000519449.5',
                    'ENST00000519527.5',
                    'ENST00000520071.1',
                    'ENST00000520903.1',
                    'ENST00000522182.1',
                    'ENST00000522369.5',
                    'ENST00000523167.1',
                    'ENST00000523255.5',
                    'ENST00000523481.5',
                    'ENST00000523644.1',
                    'ENST00000524233.1'
                ],
                'tpm': 9.34,
                'fpkm': 14.49
            },
            'file': {
                '@id': '/files/ENCFF241WYH/',
                'assay_title': 'polyA plus RNA-seq',
                'assembly': 'GRCh38',
                'biosample_ontology': {
                    'organ_slims': ['musculature of body'],
                    'term_name': 'muscle of trunk',
                    'synonyms': [
                        'torso muscle organ',
                        'trunk musculature',
                        'trunk muscle',
                        'muscle of trunk',
                        'muscle organ of torso',
                        'trunk muscle organ',
                        'muscle organ of trunk',
                        'body musculature'
                    ],
                    'name': 'tissue_UBERON_0001774',
                    'term_id': 'UBERON:0001774',
                    'classification': 'tissue'
                },
                'dataset': '/experiments/ENCSR906HEV/',
                'donors': ['/human-donors/ENCDO676JUB/'],
                'genome_annotation': 'V29'
            },
            'dataset': {
                '@id': '/experiments/ENCSR906HEV/',
                'biosample_summary': 'muscle of trunk tissue female embryo (113 days)',
                'replicates': [
                    {
                        'library': {
                            'biosample': {
                                'age_units': 'day',
                                'sex': 'female',
                                'age': '113'
                            }
                        }
                    }
                ]
            },
            'gene': {
                'geneid': '25897',
                'symbol': 'RNF19A',
                'name': 'ring finger protein 19A, RBR E3 ubiquitin protein ligase',
                'synonyms': ['DKFZp566B1346', 'RNF19', 'dorfin'],
                '@id': '/genes/25897/',
                'title': 'RNF19A (Homo sapiens)'
            },
            '@id': '/files/ENCFF241WYH/',
            '@type': ['RNAExpression', 'Item'],
            'expression_id': '/expressions/ENCFF241WYH/ENSG00000034677.12/',
            '_index': 'rna-expression',
            '_type': 'rna-expression',
            'principals_allowed.view': ['system.Everyone']
        }
    }


def test_rnaseq_repository_memory_clear(as_expressions):
    from genomic_data_service.rnaseq.repository.memory import Memory
    memory = Memory()
    memory.bulk_load(as_expressions)
    assert len(memory._data) == 3
    memory.clear()
    assert len(memory._data) == 0


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


def test_rnaseq_repository_elasticsearch_bulk_load_from_files():
    from genomic_data_service.rnaseq.repository.elasticsearch import ElasticsSearch
    es = ElasticsSearch()
    es.bulk_load_from_files([])
    assert False
