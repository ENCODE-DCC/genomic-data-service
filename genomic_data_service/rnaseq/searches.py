from flask import request as current_request

from snosearch.fields import AllResponseField
from snosearch.fields import BasicReportWithFacetsResponseField
from snosearch.fields import BasicReportWithoutFacetsResponseField
from snosearch.fields import BasicSearchResponseField
from snosearch.fields import BasicSearchWithFacetsResponseField
from snosearch.fields import BasicSearchWithoutFacetsResponseField
from snosearch.fields import CachedFacetsResponseField
from snosearch.fields import ClearFiltersResponseField
from snosearch.fields import ColumnsResponseField
from snosearch.fields import DebugQueryResponseField
from snosearch.fields import FiltersResponseField
from snosearch.fields import IDResponseField
from snosearch.fields import NotificationResponseField
from snosearch.fields import SortResponseField
from snosearch.fields import TitleResponseField
from snosearch.fields import TypeOnlyClearFiltersResponseField
from snosearch.fields import TypeResponseField
from snosearch.parsers import ParamsParser
from snosearch.responses import FieldedGeneratorResponse
from snosearch.responses import FieldedResponse

from genomic_data_service.rnaseq.matrix import make_rna_expression_search_request
from genomic_data_service.rnaseq.matrix import ExpressionMatrix
from genomic_data_service.rnaseq.matrix import TPMExpressionMatrix
from genomic_data_service.rnaseq.matrix import FPKMExpressionMatrix
from genomic_data_service.searches.constants import DEFAULT_RNA_EXPRESSION_SORT
from genomic_data_service.searches.constants import RESERVED_KEYS


def rnaget_search_quick(search_request):
    rna_client = search_request.registry['RNA_CLIENT']
    fr = FieldedResponse(
        _meta={
            'params_parser': ParamsParser(
                search_request
            )
        },
        response_fields=[
            BasicSearchResponseField(
                client=rna_client,
                default_item_types=[
                    'RNAExpression',
                ],
                reserved_keys=RESERVED_KEYS,
            ),
            DebugQueryResponseField(),
        ]
    )
    return fr.render()


def rnaget_search(search_request):
    rna_client = search_request.registry['RNA_CLIENT']
    fr = FieldedResponse(
        _meta={
            'params_parser': ParamsParser(
                search_request
            )
        },
        response_fields=[
            TitleResponseField(
                title='RNA expression search'
            ),
            TypeResponseField(
                at_type=['RNAExpressionSearch']
            ),
            IDResponseField(),
            CachedFacetsResponseField(
                client=rna_client,
                default_item_types=[
                    'RNAExpression',
                ],
                reserved_keys=RESERVED_KEYS,
            ),
            BasicSearchWithoutFacetsResponseField(
                client=rna_client,
                default_item_types=[
                    'RNAExpression',
                ],
                default_sort=DEFAULT_RNA_EXPRESSION_SORT,
                reserved_keys=RESERVED_KEYS,
            ),
            AllResponseField(),
            NotificationResponseField(),
            FiltersResponseField(),
            ClearFiltersResponseField(),
            ColumnsResponseField(),
            SortResponseField(),
            DebugQueryResponseField()
        ]
    )
    return fr.render()


def rnaget_report(search_request):
    rna_client = search_request.registry['RNA_CLIENT']
    fr = FieldedResponse(
        _meta={
            'params_parser': ParamsParser(
                search_request
            )
        },
        response_fields=[
            TitleResponseField(
                title='RNA expression report'
            ),
            TypeResponseField(
                at_type=['RNAExpressionReport']
            ),
            IDResponseField(),
            CachedFacetsResponseField(
                client=rna_client,
                default_item_types=[
                    'RNAExpression',
                ],
                reserved_keys=RESERVED_KEYS,
            ),
            BasicReportWithoutFacetsResponseField(
                client=rna_client,
                default_item_types=[
                    'RNAExpression'
                ],
                default_sort=DEFAULT_RNA_EXPRESSION_SORT,
                reserved_keys=RESERVED_KEYS,
            ),
            AllResponseField(),
            NotificationResponseField(),
            FiltersResponseField(),
            TypeOnlyClearFiltersResponseField(),
            ColumnsResponseField(),
            SortResponseField(),
            DebugQueryResponseField()
        ]
    )
    return fr.render()


def rna_expression_search_generator(search_request):
    '''
    For internal use (no view). Like search_quick but returns raw generator
    of search hits in @graph field.
    '''
    rna_client = search_request.registry['RNA_CLIENT']
    fgr = FieldedGeneratorResponse(
        _meta={
            'params_parser': ParamsParser(
                search_request
            )
        },
        response_fields=[
            BasicSearchResponseField(
                client=rna_client,
                default_item_types=[
                    'RNAExpression',
                ],
                reserved_keys=RESERVED_KEYS,
            )
        ]
    )
    return fgr.render()


def rnaget_expression_search(search_request):
    search_request = make_rna_expression_search_request(search_request)
    return rna_expression_search_generator(search_request)['@graph']


def load_matrix(search_request, matrix_class):
    expression_array = rnaget_expression_search(search_request)
    matrix = matrix_class()
    matrix.from_array(expression_array)
    return matrix


def rnaget_expression_matrix(search_request):
    em = load_matrix(search_request, ExpressionMatrix)
    return em.as_response()


def rnaget_expression_matrix_with_url(search_request):
    em = load_matrix(search_request, ExpressionMatrix)
    em.add_comment(current_request.url)
    return em.as_response()


def rnaget_tpm_expression_matrix_with_url(search_request):
    tem = load_matrix(search_request, TPMExpressionMatrix)
    tem.add_comment(current_request.url)
    return tem.as_response()


def rnaget_fpkm_expression_matrix_with_url(search_request):
    fem = load_matrix(search_request, FPKMExpressionMatrix)
    fem.add_comment(current_request.url)
    return fem.as_response()
