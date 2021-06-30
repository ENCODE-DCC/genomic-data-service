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
