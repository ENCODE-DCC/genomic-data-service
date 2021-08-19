from genomic_data_service import app
from genomic_data_service.searches.constants import DEFAULT_RNA_EXPRESSION_SORT
from genomic_data_service.searches.constants import RESERVED_KEYS
from genomic_data_service.searches.requests import make_search_request

from snosearch.fields import AllResponseField
from snosearch.fields import BasicSearchResponseField
from snosearch.fields import BasicSearchWithFacetsResponseField
from snosearch.fields import ClearFiltersResponseField
from snosearch.fields import ColumnsResponseField
from snosearch.fields import DebugQueryResponseField
from snosearch.fields import FiltersResponseField
from snosearch.fields import IDResponseField
from snosearch.fields import NotificationResponseField
from snosearch.fields import SortResponseField
from snosearch.fields import TitleResponseField
from snosearch.fields import TypeResponseField
from snosearch.parsers import ParamsParser
from snosearch.responses import FieldedResponse


@app.route('/rnaget-search/', methods=['GET'])
def rnaget_search():
    search_request = make_search_request()
    rna_client = search_request.registry['RNA_CLIENT']
    # Note the order of rendering matters for some fields, e.g. AllResponseField and
    # NotificationResponseField depend on results from BasicSearchWithFacetsResponseField.
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
                at_type=['RNAExpression']
            ),
            IDResponseField(),
            BasicSearchWithFacetsResponseField(
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
