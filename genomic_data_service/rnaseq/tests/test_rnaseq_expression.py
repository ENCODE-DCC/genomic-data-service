import pytest


def test_rnaseq_expression_init():
    from genomic_data_service.rnaseq.domain.expression import Expression
    data = [
        'POMC',
        'ENST000, ENST001',
        0.03,
        90.1,
    ]
    expression = Expression(
        *data
    )
    assert isinstance(expression, Expression)
    assert expression.gene_id == 'POMC'
    assert expression.transcript_ids == 'ENST000, ENST001'
    assert expression.tpm == 0.03
    assert expression.fpkm == 90.1


def test_rnaseq_expression_dict():
    from genomic_data_service.rnaseq.domain.expression import Expression
    data = [
        'POMC',
        'ENST000, ENST001',
        0.03,
        90.1,
    ]
    expression = Expression(
        *data
    )
    assert expression.__dict__ == {
        'fpkm': 90.1,
        'gene_id': 'POMC',
        'tpm': 0.03,
        'transcript_ids': 'ENST000, ENST001'
    }


def test_rnaseq_expression_as_dict():
    from genomic_data_service.rnaseq.domain.expression import Expression
    data = [
        'POMC',
        'ENST000, ENST001',
        '0.03',
        90.1,
    ]
    expression = Expression(
        *data
    )
    assert expression.as_dict() == {
        'fpkm': 90.1,
        'gene_id': 'POMC',
        'tpm': 0.03,
        'transcript_ids': ['ENST000', 'ENST001'],
    }


def test_rnaseq_expression_remove_version_from_gene_id():
    from genomic_data_service.rnaseq.domain.expression import remove_version_from_gene_id
    assert remove_version_from_gene_id('ENSG00000224939') == 'ENSG00000224939'
    assert remove_version_from_gene_id('ENSG00000224939.14') == 'ENSG00000224939'


def test_rnaseq_expression_gene_id_without_version():
    from genomic_data_service.rnaseq.domain.expression import Expression
    data = [
        'ENSG00000034677.12',
        'ENST000, ENST001',
        0.03,
        90.1,
    ]
    expression = Expression(
        *data
    )
    assert expression.gene_id_without_version == 'ENSG00000034677'


def test_rnaseq_expression_expressions_init(mock_portal):
    from genomic_data_service.rnaseq.expressions import Expressions
    from genomic_data_service.rnaseq.repository.memory import Memory
    repository = Memory()
    portal = mock_portal
    expressions = Expressions(portal, repository)
    assert isinstance(expressions, Expressions)


def test_rnaseq_expression_prefix_numerical_gene_id():
    from genomic_data_service.rnaseq.domain.expression import prefix_numerical_gene_id
    assert prefix_numerical_gene_id('ENSG00000224939') == 'ENSG00000224939'
    assert prefix_numerical_gene_id('ENSG00000224939.14') == 'ENSG00000224939.14'
    assert prefix_numerical_gene_id('21301') == 'tRNAscan:21301'
    assert prefix_numerical_gene_id('32719') == 'tRNAscan:32719'
    assert prefix_numerical_gene_id(21301) == 'tRNAscan:21301'
