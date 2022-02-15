from genomic_data_service.rnaseq.remote.portal import get_json
from genomic_data_service.rnaseq.rnaget.constants import BASE_SEARCH_URL
from genomic_data_service.rnaseq.rnaget.constants import DATASET_FILTERS
from genomic_data_service.searches.requests import make_search_request


from snosearch.parsers import QueryString


def get_studies(filters=None):
    filters = filters or []
    qs = QueryString(
        make_search_request()
    )
    qs.extend(
        DATASET_FILTERS + filters
    )
    url = (
        f'{BASE_SEARCH_URL}'
        f'?{qs.get_query_string()}'
    )
    return get_json(url)
