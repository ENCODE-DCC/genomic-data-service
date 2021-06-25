import pytest


def test_rnaseq_expressions_init():
    from genomic_data_service.rnaseq.domain.expressions import Expressions
    expressions = Expressions({}, {})
    assert isinstance(expressions, Expressions)
