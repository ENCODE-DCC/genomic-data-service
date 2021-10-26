import os

from genomic_data_service.rnaseq.domain.expression import Expression
from genomic_data_service.rnaseq.remote.tsv import local_tsv_iterable
from genomic_data_service.rnaseq.remote.tsv import maybe_save_file
from genomic_data_service.rnaseq.domain.constants import AT_ID
from genomic_data_service.rnaseq.domain.constants import AT_TYPE
from genomic_data_service.rnaseq.domain.constants import BASE_PATH
from genomic_data_service.rnaseq.domain.constants import DATASET
from genomic_data_service.rnaseq.domain.constants import DATASETS
from genomic_data_service.rnaseq.domain.constants import DATASET_FIELDS
from genomic_data_service.rnaseq.domain.constants import DOCUMENT_PREFIX
from genomic_data_service.rnaseq.domain.constants import DOMAIN
from genomic_data_service.rnaseq.domain.constants import EXPRESSION_AT_TYPE
from genomic_data_service.rnaseq.domain.constants import EXPRESSION_ID
from genomic_data_service.rnaseq.domain.constants import FILE_FIELDS
from genomic_data_service.rnaseq.domain.constants import GENES
from genomic_data_service.rnaseq.domain.constants import INDEXING_FIELDS


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


def remove_version_from_gene_id(gene_id):
    return gene_id.split('.')[0]


class RnaSeqFile:

    BASE_PATH = BASE_PATH
    DOMAIN = DOMAIN
    FILE_FIELDS = FILE_FIELDS
    DATASET_FIELDS = DATASET_FIELDS
    
    def __init__(self, props, repositories):
        self.props = props
        self.repositories = repositories

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

    def _extract_dataset_properties(self):
        dataset = self.repositories.get(
            DATASETS,
            {}
        ).get(
            self._file_properties.get(DATASET),
            {}
        )
        self._dataset_properties = {
            k: v
            for k, v in dataset.items()
            if k in self.DATASET_FIELDS
        }

    def _get_gene_from_gene_id(self, gene_id):
        return self.repositories.get(
            GENES,
            {}
        ).get(
            gene_id,
            {}
        )

    def _get_expression_id(self, gene_id):
        accession = self.props['@id'].split('/')[2]
        return f'/expressions/{accession}/{gene_id}/'

    def _get_at_fields(self, gene_id):
        return {
            AT_ID: self._get_expression_id(gene_id),
            AT_TYPE: EXPRESSION_AT_TYPE,
        }

    def _get_indexing_fields(self, gene_id):
        return {
            '_id': self._get_expression_id(gene_id),
            **INDEXING_FIELDS
        }

    def _build_document(self, expression):
        return {
            DOCUMENT_PREFIX: {
                'expression': expression.as_dict(),
                'file': self._file_properties,
                'dataset': self._dataset_properties,
                'gene': self._get_gene_from_gene_id(
                    expression.gene_id_without_version
                ),
                **self._get_at_fields(
                    expression.gene_id
                )
            },
            **self._get_indexing_fields(
                expression.gene_id
            ),
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

    def _get_documents(self):
        for expression in self._get_expressions():
            yield self._build_document(expression)


    def as_documents(self):
        self._extract_file_properties()
        self._extract_dataset_properties()
        return (
            document
            for document in self._get_documents()
        )
