from .expression import Expression
import os

from genomic_data_service.rnaseq.domain.expression import Expression
from genomic_data_service.rnaseq.remote.tsv import local_tsv_iterable
from genomic_data_service.rnaseq.remote.tsv import maybe_save_file
from genomic_data_service.rnaseq.domain.constants import BASE_PATH
from genomic_data_service.rnaseq.domain.constants import DOCUMENT_PREFIX
from genomic_data_service.rnaseq.domain.constants import DOMAIN
from genomic_data_service.rnaseq.domain.constants import FILE_FIELDS


ROW_VALUES = [
    'gene_id',
    'transcript_id(s)',
    'TPM',
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
    tsv, _, indices = get_tsv_header_and_indices(
        url,
        path
    )
    for row in tsv:
        yield get_values_from_row(row, indices)


class RnaSeqFile:

    BASE_PATH = BASE_PATH
    DOMAIN = DOMAIN
    FILE_FIELDS = FILE_FIELDS
    
    def __init__(self, props):
        self.props = props

    @property
    def url(self):
        return self.DOMAIN + self.props.get('href')

    @property
    def path(self):
        return self.BASE_PATH + self.url.split('/')[-1]

    def _extract_file_properties(self):
        self._file_properties = {
            k: v
            for k, v in self.props.items()
            if k in self.FILE_FIELDS
        }

    def _get_expressions(self):
        expressions = get_expression_generator(
            self.url,
            self.path,
        )
        return (
            Expression(*row)
            for row in expressions
        )

    def as_expressions():
        documents = [{}]
        return (
            {
                DOCUMENT_PREFIX: document
            }
            for document in documents
        )
