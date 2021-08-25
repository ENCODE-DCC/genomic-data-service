from genomic_data_service import app
from genomic_data_service.rnaseq.matrix import ExpressionMatrix
from genomic_data_service.rnaseq.matrix import get_rna_expression_search_request
from genomic_data_service.searches.constants import DEFAULT_RNA_EXPRESSION_SORT
from genomic_data_service.searches.constants import RESERVED_KEYS
from genomic_data_service.searches.requests import make_search_request

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


@app.route('/rnaget-search-quick/', methods=['GET'])
def rnaget_search_quick():
    search_request = make_search_request()
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


@app.route('/rnaget-search/', methods=['GET'])
def rnaget_search():
    search_request = make_search_request()
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


@app.route('/rnaget-report/', methods=['GET'])
def rnaget_report():
    search_request = make_search_request()
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


@app.route('/rnaget-expression-matrix/', methods=['GET'])
def rnaget_expression_matrix():
    search_request = get_rna_expression_search_request(make_search_request())
    expression_array = rna_expression_search_generator(search_request)['@graph']
    em = ExpressionMatrix()
    em.from_array(expression_array)
    return em.as_response()
