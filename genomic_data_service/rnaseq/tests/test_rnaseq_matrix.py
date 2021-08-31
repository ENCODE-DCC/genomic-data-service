import pytest


EXPRESSION_ARRAY = [
    {
        "expression": {
            "tpm": 14.1,
            "gene_id": "ENSG00000102974.15"
        },
        "file": {
            "@id": "/files/ENCFF004JWA/"
        },
        "dataset": {
            "biosample_summary": "ABC"
        },
        "gene": {
            "symbol": "CTCF"
        }
    },
    {
        "expression": {
            "tpm": 0.0,
            "gene_id": "ENSG00000115138.10"
        },
        "file": {
            "@id": "/files/ENCFF004JWA/"
        },
        "dataset": {
            "biosample_summary": "ABC"
        },
        "gene": {
            "symbol": "POMC"
        }
    },
    {
        "expression": {
            "tpm": 19.19,
            "gene_id": "ENSG00000100393.12"
        },
        "file": {
            "@id": "/files/ENCFF004JWA/"
        },
        "dataset": {
            "biosample_summary": "ABC"
        },
        "gene": {
            "symbol": "EP300"
        }
    },
    {
        "expression": {
            "tpm": 75.65,
            "gene_id": "ENSG00000100393.12"
        },
        "file": {
            "@id": "/files/ENCFF006IHP/"
        },
        "dataset": {
            "biosample_summary": "DEF"
        },
        "gene": {
            "symbol": "EP300"
        }
    },
    {
        "expression": {
            "tpm": 55.53,
            "gene_id": "ENSG00000102974.15"
        },
        "file": {
            "@id": "/files/ENCFF006IHP/"
        },
        "dataset": {
            "biosample_summary": "DEF"
        },
        "gene": {
            "symbol": "CTCF"
        }
    },
    {
        "expression": {
            "tpm": 2.94,
            "gene_id": "ENSG00000115138.10"
        },
        "file": {
            "@id": "/files/ENCFF006IHP/"
        },
        "dataset": {
            "biosample_summary": "DEF"
        },
        "gene": {
            "symbol": "POMC"
        }
    },
    {
        "expression": {
            "tpm": 8.0,
            "gene_id": "ENSG00000100393.12"
        },
        "file": {
            "@id": "/files/ENCFF008KUV/"
        },
        "dataset": {
            "biosample_summary": "GHI"
        },
        "gene": {
            "symbol": "EP300"
        }
    },
    {
        "expression": {
            "tpm": 0.02,
            "gene_id": "ENSG00000115138.10"
        },
        "file": {
            "@id": "/files/ENCFF008KUV/"
        },
        "dataset": {
            "biosample_summary": "GHI"
        },
        "gene": {
            "symbol": "POMC"
        }
    },
    {
        "expression": {
            "tpm": 16.36,
            "gene_id": "ENSG00000102974.15"
        },
        "file": {
            "@id": "/files/ENCFF008KUV/"
        },
        "dataset": {
            "biosample_summary": "GHI"
        },
        "gene": {
            "symbol": "CTCF"
        }
    }
]


def test_reports_expressions_matrix_expression_matrix_init():
    from genomic_data_service.rnaseq.matrix import ExpressionMatrix
    em = ExpressionMatrix()
    assert isinstance(em, ExpressionMatrix)


def test_reports_expressions_matrix_expression_matrix_from_array():
    from genomic_data_service.rnaseq.matrix import ExpressionMatrix
    em = ExpressionMatrix()
    em.from_array(EXPRESSION_ARRAY)
    expected_columns = [
        ('/files/ENCFF004JWA/', 'ABC'),
        ('/files/ENCFF006IHP/', 'DEF'),
        ('/files/ENCFF008KUV/', 'GHI'),
    ]
    expected_rows = [
        ('ENSG00000100393.12', 'EP300'),
        ('ENSG00000102974.15', 'CTCF'),
        ('ENSG00000115138.10', 'POMC'),
    ]
    expected_groups = {
        (('ENSG00000102974.15', 'CTCF'), ('/files/ENCFF004JWA/', 'ABC',)): 14.1,
        (('ENSG00000115138.10', 'POMC'), ('/files/ENCFF004JWA/', 'ABC',)): 0.0,
        (('ENSG00000100393.12', 'EP300'), ('/files/ENCFF004JWA/', 'ABC',)): 19.19,
        (('ENSG00000100393.12', 'EP300'), ('/files/ENCFF006IHP/', 'DEF',)): 75.65,
        (('ENSG00000102974.15', 'CTCF'), ('/files/ENCFF006IHP/', 'DEF',)): 55.53,
        (('ENSG00000115138.10', 'POMC'), ('/files/ENCFF006IHP/', 'DEF',)): 2.94,
        (('ENSG00000100393.12', 'EP300'), ('/files/ENCFF008KUV/', 'GHI',)): 8.0,
        (('ENSG00000115138.10', 'POMC'), ('/files/ENCFF008KUV/', 'GHI',)): 0.02,
        (('ENSG00000102974.15', 'CTCF'), ('/files/ENCFF008KUV/', 'GHI',)): 16.36,
    }
    assert list(sorted(em.columns)) == expected_columns
    assert list(sorted(em.rows)) == expected_rows
    assert em.groups == expected_groups


def test_reports_expressions_matrix_expression_matrix_as_matrix():
    from genomic_data_service.rnaseq.matrix import ExpressionMatrix
    em = ExpressionMatrix()
    em.from_array(EXPRESSION_ARRAY)
    matrix = list(em.as_matrix())
    expected_matrix = [
        ['featureID', 'geneSymbol', '/files/ENCFF004JWA/, ABC', '/files/ENCFF006IHP/, DEF', '/files/ENCFF008KUV/, GHI'],
        ['ENSG00000102974.15', 'CTCF', 14.1, 55.53, 16.36],
        ['ENSG00000100393.12', 'EP300', 19.19, 75.65, 8.0],
        ['ENSG00000115138.10', 'POMC', 0.0, 2.94, 0.02]
    ]
    assert matrix == expected_matrix


def test_reports_expressions_matrix_expression_matrix_as_tsv():
    from genomic_data_service.rnaseq.matrix import ExpressionMatrix
    em = ExpressionMatrix()
    em.from_array(EXPRESSION_ARRAY)
    actual_tsv = list(em.as_tsv())
    expected_tsv = [
        b'featureID\tgeneSymbol\t/files/ENCFF004JWA/, ABC\t/files/ENCFF006IHP/, DEF\t/files/ENCFF008KUV/, GHI\n',
        b'ENSG00000102974.15\tCTCF\t14.1\t55.53\t16.36\n',
        b'ENSG00000100393.12\tEP300\t19.19\t75.65\t8.0\n',
        b'ENSG00000115138.10\tPOMC\t0.0\t2.94\t0.02\n'
    ]
    assert actual_tsv == expected_tsv


def test_reports_expressions_matrix_range_expression_matrix_as_matrix():
    from collections import Counter
    from genomic_data_service.rnaseq.matrix import RangeExpressionMatrix
    rem = RangeExpressionMatrix()
    rem.from_array(EXPRESSION_ARRAY)
    matrix = list(rem.as_matrix())
    expected_matrix = [
        ['featureID', 'geneSymbol', '/files/ENCFF004JWA/, ABC', '/files/ENCFF006IHP/, DEF', '/files/ENCFF008KUV/, GHI'],
        ['ENSG00000102974.15', 'CTCF', 14.1, 55.53, 16.36],
        ['ENSG00000100393.12', 'EP300', 19.19, 75.65, 8.0],
        ['ENSG00000115138.10', 'POMC', 0.0, 2.94, 0.02]
    ]
    assert matrix == expected_matrix
    assert len(EXPRESSION_ARRAY) == 9
    FILTERED_EXPRESSION_ARRAY = [
        expression
        for expression in EXPRESSION_ARRAY
        if expression['expression']['tpm'] > 1.5
    ]
    assert len(FILTERED_EXPRESSION_ARRAY) == 7
    symbol_count = Counter([
        expression['gene']['symbol']
        for expression in FILTERED_EXPRESSION_ARRAY
    ])
    assert symbol_count['POMC'] == 1
    assert symbol_count['CTCF'] == 3
    assert symbol_count['EP300'] == 3
    rem = RangeExpressionMatrix()
    rem.from_array(FILTERED_EXPRESSION_ARRAY)
    matrix = list(rem.as_matrix())
    expected_matrix = [
        ['featureID', 'geneSymbol', '/files/ENCFF004JWA/, ABC', '/files/ENCFF006IHP/, DEF', '/files/ENCFF008KUV/, GHI'],
        ['ENSG00000102974.15', 'CTCF', 14.1, 55.53, 16.36],
        ['ENSG00000100393.12', 'EP300', 19.19, 75.65, 8.0]
    ]
    assert matrix == expected_matrix
    FILTERED_EXPRESSION_ARRAY = [
        expression
        for expression in EXPRESSION_ARRAY
        if expression['expression']['tpm'] < 75
    ]
    assert len(FILTERED_EXPRESSION_ARRAY) == 8
    rem = RangeExpressionMatrix()
    rem.from_array(FILTERED_EXPRESSION_ARRAY)
    matrix = list(rem.as_matrix())
    expected_matrix = [
        ['featureID', 'geneSymbol', '/files/ENCFF004JWA/, ABC', '/files/ENCFF006IHP/, DEF', '/files/ENCFF008KUV/, GHI'],
        ['ENSG00000102974.15', 'CTCF', 14.1, 55.53, 16.36],
        ['ENSG00000115138.10', 'POMC', 0.0, 2.94, 0.02]
    ]
