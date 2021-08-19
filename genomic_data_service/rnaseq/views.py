from genomic_data_service import app
from genomic_data_service.searches.constants import RESERVED_KEYS
from genomic_data_service.searches.requests import make_search_request

from snosearch.fields import BasicSearchResponseField
from snosearch.fields import DebugQueryResponseField
from snosearch.parsers import ParamsParser
from snosearch.responses import FieldedResponse


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
