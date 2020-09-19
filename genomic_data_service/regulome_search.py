from datetime import datetime
from flask import jsonify, request
from werkzeug.exceptions import BadRequest

from genomic_data_service import es, app
from genomic_data_service.rsid_coordinates_resolver import get_coordinates, resolve_coordinates_and_variants
from genomic_data_service.constants import GENOME_TO_ALIAS
from genomic_data_service.regulome_atlas_utils import extract_search_params
from genomic_data_service.regulome_atlas import RegulomeAtlas


def build_response(block):
    response = {
        '@context': '/terms',
        '@id': request.full_path,
        '@type': ['regulome-search'],
        'title': 'RegulomeDB search',
    }

    return jsonify(response.update(block))

def error_response(error_msg):
    return build_response({
        'notifications': {
            'Failed': error_msg
        }
    })

def validate_search_request(request):
    args = request.args

    if 'from' in args or 'size' in args:
        return (False, 'Invalid parameters: "from" and "size" are not accepted.')

    return (True, None)


@app.route('/regulome-search', methods=['GET'])
def regulome_search():
    """
    Regulome peak analysis for a single region.
    Ex params:
       genome=GRCh37
       regions=chr2%3A754011-754012
       format=json
    """

    valid, error_msg = validate_search_request(request)

    if not valid:
        raise BadRequest(error_msg)

    assembly, from_, size, format_, maf, region_queries = extract_search_params(
        request.params
    )

    atlas = RegulomeAtlas(es)
    
    variants, query_coordinates, notifications = resolve_coordinates_and_variants(region_queries, assembly, atlas, maf)

    total = len(variants)
    from_ = max(from_, 0)

    if size in ('all', ''):
        to_ = total
    else:
        try:
            size = int(size)
        except ValueError:
            size = 200
        to_ = min(from_ + max(size, 0), total)

    result = {
        'timing': [{'parse_region_query': (time.time() - begin)}],
        'assembly': assembly,
        'query_coordinates': query_coordinates,
        'format': format_,
        'from': from_,
        'total': total,
        'variants': [
            {
                'chrom': chrom,
                'start': start,
                'end': end,
                'rsids': sorted(variants[(chrom, start, end)])
            }
            for chrom, start, end in sorted(variants)[from_:to_]
        ],
        'notifications': notifications,
    }

    if len(result['query_coordinates']) != 1:
        result['notifications'] = {
            'Failed': 'Received {} region queries. Exact one region or one '
            'variant can be processed by regulome-search'.format(
                len(result['query_coordinates'])
            )
        }
        return build_response(result)

    regulome_score, features, notifications, graph, timing, nearby_snps = search_peaks(
        query_coordinates,
        atlas,
        assembly,
        len(result['variants'])
    )

    result['regulome_score'] = regulome_score
    result['features'] = features
    result['notifications'].update(notifications)
    result['@graph'] = graph
    result['timing'] += timing
    result['nearby_snps'] = nearby_snps

    return build_response(result)
