import numpy as np

from flask import Response

from genomic_data_service.reports.csv import CSVGenerator
from genomic_data_service.searches.requests import make_search_request
from snosearch.parsers import QueryString


def extract_value(expression, key, default=''):
    value = expression
    for field in key:
        value = value.get(field, {})
    if isinstance(value, dict):
        value = default
    return value


def extract_values(expression, keys):
    return tuple(
        extract_value(expression, key)
        for key in keys
    )


def join_tuples(values, sep=', '):
    return [
        sep.join(value) if isinstance(value, tuple) else value
        for value in
        values
    ]


class ExpressionMatrix:
    '''
    Naive implementation of pivoting a table in order to make an 
    expression matrix from an array of expression values. Requires
    pulling all expression values into memory.
    '''

    BASE_COLUMNS = [
        'featureID',
        'geneSymbol',
    ]

    ROW_KEYS = (
        ('expression', 'gene_id'),
        ('gene', 'symbol'),
    )

    COLUMN_KEYS = (
        ('file', '@id'),
        ('dataset', 'biosample_summary'),
    )

    # Only supporting single value and no agg function for now,
    # which means (row, column) key must point to unique value.
    VALUE_KEY = (
        'expression',
        'tpm',
    )

    FILL_VALUE = 0.0
    MIMETYPE = 'text/tsv'
    CONTENT_DISPOSITION = (
        'Content-Disposition',
        'attachment; filename="expression.tsv"'
    )

    def __init__(self):
        self.columns = set()
        self.rows = set()
        self.groups = {}
        self.csv = CSVGenerator()

    def _groupby(self, row, column, value):
        self.rows.add(row)
        self.columns.add(column)
        self.groups[(row, column)] = value

    def from_array(self, array):
        for expression in array:
            row = extract_values(
                expression,
                self.ROW_KEYS
            )
            column = extract_values(
                expression,
                self.COLUMN_KEYS
            )
            value = extract_value(
                expression,
                self.VALUE_KEY,
            )
            self._groupby(row, column, value)

    def as_matrix(self):
        # Could allow custom sorting by row, column, or values.
        # Would probably require storing data as tuples, sorting
        # tuples by position, then building up column and row values
        # based on resulting tuples in a way that maintains order.
        sorted_column_keys = list(sorted(self.columns))
        sorted_row_keys = list(
            sorted(self.rows, key=lambda row: (row[1], row[0]))
        )
        yield self.BASE_COLUMNS + join_tuples(sorted_column_keys)
        for row_key in sorted_row_keys:
            row = join_tuples(row_key)
            for column_key in sorted_column_keys:
                row.append(
                    self.groups.get(
                        (
                            row_key,
                            column_key,
                        ),
                        self.FILL_VALUE
                    )
                )
            yield row

    def as_tsv(self):
        for row in self.as_matrix():
            yield self.csv.writerow(row)

    def as_response(self):
        return Response(
            self.as_tsv(),
            mimetype=self.MIMETYPE,
            headers=[
                self.CONTENT_DISPOSITION,
            ]
        )


class RangeExpressionMatrix(ExpressionMatrix):
    '''
    Like ExpressionMatrix but drops rows with NaN. This allows returning matrix
    where features are filtered by threshold values.
    '''
    FILL_VALUE = np.nan

    def as_matrix(self):
        for row in super().as_matrix():
            if self.FILL_VALUE in row:
                continue
            yield row


RNA_EXPRESSION_DEFAULT_PARAMS = [
    ('field', 'expression.gene_id'),
    ('field', 'file.@id'),
    ('field', 'dataset.biosample_summary'),
    ('field', 'gene.symbol'),
    ('field', 'expression.tpm'),
    ('limit', 'all'),
]


def make_rna_expression_search_request(search_request):
    qs = QueryString(search_request)
    qs.drop('field')
    qs.drop('limit')
    qs.extend(RNA_EXPRESSION_DEFAULT_PARAMS)
    return make_search_request(
        qs.get_request_with_new_query_string()
    )
