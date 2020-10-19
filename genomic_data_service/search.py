import time
from flask import jsonify, request
from werkzeug.exceptions import BadRequest
from genomic_data_service import es, app
from genomic_data_service.regulome_atlas import RegulomeAtlas
from genomic_data_service.rsid_coordinates_resolver import get_coordinates, resolve_coordinates_and_variants, search_peaks
from genomic_data_service.request_utils import validate_search_request, extract_search_params


def build_response(block):
    return {
        **block, **{
        '@context': '/terms/',
        '@id': request.full_path,
        '@type': ['search'],
        'title': 'Genomic Region Search',
        }
    }

@app.route('/search/', methods=['GET'])
def search():
    """
    Peak analysis for a single region.
    Ex params:
       genome=GRCh37
       regions=chr2%3A754011-754012
       format=json
    """

    begin = time.time()

    valid, error_msg = validate_search_request(request)

    if not valid:
        raise BadRequest(error_msg)
    
    assembly, from_, size, format_, maf, region_queries = extract_search_params(
        request.args
    )

    atlas = RegulomeAtlas(es)
    
    variants, query_coordinates, notifications = resolve_coordinates_and_variants(
        region_queries, assembly, atlas, maf
    )

    total = len(variants)
    from_ = max(from_, 0)

    if size in ('all', ''):
        to_ = total
    else:
        try:
            size = int(size)
        except:
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
        'notifications': notifications
    }

    if len(query_coordinates) != 1:
        result['notifications'] = {
            'Failed': 'Received {} region queries. Exact one region or one '
            'variant can be processed by regulome-search'.format(
                len(query_coordinates)
            )
        }
        return jsonify(build_response(result))

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

    return jsonify(build_response(result))
