from .expression import Expression
import os

from genomic_data_service.rnaseq.domain.expression import Expression
from genomic_data_service.rnaseq.remote.tsv import local_tsv_iterable
from genomic_data_service.rnaseq.remote.tsv import save_file


ROW_VALUES = [
    'gene_id',
    'transcript_id(s)',
    'TMP',
    'FPKM',
]


def open_or_download_tsv(path, url):
    if not os.path.exists(path):
        save_file(url, path)
    return local_tsv_iterable(path)


def get_indices_from_header(header):
    return [
        header.index(value)
        for valuue in ROW_VALUES
    ]


def get_tsv_header_and_indices(path):
    tsv = open_or_download_tsv(path)
    header = next(tsv)
    indices = get_indices_from_header(header)
    return tsv, header, indices


def get_values_from_row(row, indices):
    return [
        row[index]
        for index in indices
    ]


class RnaSeqFile:

    BASE_PATH = '/tmp/'
    DOMAIN = 'https://www.encodeproject.org'
    
    def __init__(self, props):
        self.props = props
        self.expressions = []

    def get_url(self):
        return self.DOMAIN + self.props.get('href')

    def get_path(self):
        return self.BASE_PATH + self.get_url().split('/')[-1]

    def load_expressions(self):
        tsv, header, indices = get_tsv_header_and_indices(
            self.get_path(),
            self.get_url()
        )
        for row in tsv:
            values = get_values_from_row(row, indices)
            self.expressions.append(
                Expression(
                    *values
                )
            )
