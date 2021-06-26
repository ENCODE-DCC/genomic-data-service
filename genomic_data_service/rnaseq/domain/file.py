from .expression import Expression
import os

from genomic_data_service.rnaseq.domain.expression import Expression
from genomic_data_service.rnaseq.remote.tsv import local_tsv_iterable
from genomic_data_service.rnaseq.remote.tsv import maybe_save_file


ROW_VALUES = [
    'gene_id',
    'transcript_id(s)',
    'TMP',
    'FPKM',
]


def download_and_open_tsv(url, path):
    maybe_save_file(url, path)
    return local_tsv_iterable(path)


def get_indices_from_header(header):
    return [
        header.index(value)
        for value in ROW_VALUES
    ]


def get_tsv_header_and_indices(url, path):
    tsv = download_and_open_tsv(url, path)
    header = next(tsv)
    indices = get_indices_from_header(header)
    return tsv, header, indices


def get_values_from_row(row, indices):
    return [
        row[index]
        for index in indices
    ]


def get_expression_generator(url, path):
    tsv, header, indices = get_tsv_header_and_indices(
        url,
        path
    )
    yield header
    for row in tsv:
        yield get_values_from_row(row, indices)


class RnaSeqFile:

    BASE_PATH = '/tmp/'
    DOMAIN = 'https://www.encodeproject.org'
    
    def __init__(self, props):
        self.props = props
        self.expressions = []

    @property
    def url(self):
        return self.DOMAIN + self.props.get('href')

    @property
    def path(self):
        return self.BASE_PATH + self.get_url().split('/')[-1]

    def load_expressions(self):
        expressions = get_expression_generator(
            self.url,
            self.path,
        )
        header = next(expressions)
        for expression in expressions:
            self.expressions.append(
                Expression(
                    *expression
                )
            )
