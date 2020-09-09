from datetime import datetime
from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch

from .rsid_coordinates_resolver import get_coordinates, resolve_coordinates_and_variants
from .constants import GENOME_TO_ALIAS
from .regulome_atlas_utils import extract_search_params
from .regulome_atlas import RegulomeAtlas

es = Elasticsearch(port=9201)

app = Flask(__name__)

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

    return (True)


@app.route('/regulome-search', methods=['GET'])
def regulome_search_original():
    """
    Regulome peak analysis for a single region.
    Ex params:
       genome=GRCh37
       regions=chr2%3A754011-754012
       format=json
    """

    valid, error_msg = validate_search_request(request)

    if not valid:
        return error_response(error_msg)

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

    # Start search
    begin = time.time()  # DEBUG: timing
    coord = query_coordinates[0]
    chrom, start_end = coord.split(':')
    start, end = start_end.split('-')
    start = int(start)
    end = int(end)

    try:
        all_hits = region_get_hits(
            atlas, assembly, chrom, start, end, peaks_too=True
        )
        evidence = atlas.regulome_evidence(
            all_hits['datasets'], chrom, start, end
        )
        result['regulome_score'] = atlas.regulome_score(
            all_hits['datasets'], evidence
        )
        result['features'] = evidence_to_features(evidence)
    except Exception as e:
        result['notifications'][coord] = 'Failed: (exception) {}'.format(e)
    peak_details = []
    for peak in all_hits.get('peaks', []):
        peak_details.append({
            'chrom': peak['_index'],
            'start': peak['_source']['coordinates']['gte'],
            'end': peak['_source']['coordinates']['lt'],
            'strand': peak['_source'].get('strand'),
            'value': peak['_source'].get('value'),

            'file': peak['resident_detail']['file']['@id'].split('/')[2],

            'dataset': peak['resident_detail']['dataset']['@id'],
            'documents': peak['resident_detail']['dataset']['documents'],
            'biosample_ontology': peak['resident_detail']['dataset']['biosample_ontology'],
            'method': peak['resident_detail']['dataset']['collection_type'],
            'targets': peak['resident_detail']['dataset'].get('target', []),
        })
    result['@graph'] = peak_details
    result['timing'].append({'regulome_search_scoring': (time.time() - begin)})  # DEBUG: timing

    begin = time.time()  # DEBUG: timing
    result['nearby_snps'] = atlas.nearby_snps(
        _GENOME_TO_ALIAS.get(assembly, 'hg19'),
        chrom,
        int((start + end) / 2),
        # No guarentee the query coordinate corresponds to one RefSNP.
        max_snps=len(result['variants'])+10
    )
    # Use nearby_snps instead
    result.pop('variants', None)
    result['timing'].append({'nearby_snps': (time.time() - begin)})  # DEBUG: timing
    
    return build_response(result)


app.run(port=5000, debug=True)
