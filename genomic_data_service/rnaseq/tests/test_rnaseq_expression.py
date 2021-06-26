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
