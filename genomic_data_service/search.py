import time
from flask import jsonify, request
from werkzeug.exceptions import BadRequest
from genomic_data_service import regulome_es, app
from genomic_data_service.region_service import RegionService
from genomic_data_service.regulome_atlas import RegulomeAtlas
from genomic_data_service.rsid_coordinates_resolver import resolve_coordinates_and_variants, search_peaks
from genomic_data_service.request_utils import validate_search_request, extract_search_params
from genomic_data_service.constants import REGULOME_VALID_ASSEMBLY, TWO_BIT_HG19_FILE_PATH, TWO_BIT_HG38_FILE_PATH
import py2bit


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
    Peak analysis for a single region. Used by RegulomeDB.
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

    if assembly not in REGULOME_VALID_ASSEMBLY:
        result = {
            'assembly': assembly,
            'format': format_,
            'from': from_,
            'notifications': {
                'Failed': 'Invalid assembly {}'.format(assembly)
            }
        }
        return jsonify(build_response(result))
    if not region_queries or len(region_queries) > 1:
        result = {
            'assembly': assembly,
            'region_queries': region_queries,
            'format': format_,
            'from': from_,
            'notifications': {
                'Failed': 'Received {} region queries. Exact one region or one '
                'variant can be processed by regulome-search'.format(
                    len(region_queries)
                )
            }
        }
        return jsonify(build_response(result))

    atlas = RegulomeAtlas(regulome_es)

    variants, query_coordinates, notifications = resolve_coordinates_and_variants(
        region_queries, assembly, atlas, maf
    )

    if notifications:
        result = {
            'assembly': assembly,
            'region_queries': region_queries,
            'format': format_,
            'from': from_,
            'notifications': notifications
        }
        return jsonify(build_response(result))

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
    }

    regulome_score, features, notifications, graph, timing, nearby_snps = search_peaks(
        query_coordinates,
        atlas,
        assembly,
        len(result['variants'])
    )
    sequence = get_sequence(assembly, query_coordinates[0])

    result['regulome_score'] = regulome_score
    result['features'] = features
    result['notifications'].update(notifications)
    result['@graph'] = graph
    result['timing'] += timing
    result['nearby_snps'] = nearby_snps
    result['sequence'] = sequence

    return jsonify(build_response(result))


# General region search endpoint, accepts any region length
@app.route('/region-search/', methods=['GET'])
def region_search():
    """
    Returns all regions matching the queried interval.
    Ex params:
       query=rs75982468 or chr10:5894499-5894500 or ENSG00000088320.3 (rsids or coordinate ranges or ensembl id)
       start=754000
       end=754012
       chr=1
       files_only = false (default)
       page=1 (default)
       limit=100 (default)
       assembly=GRCh38 (default)
       expand=0 (in kb, value used to expand the query)
       interval=[intersects, contain, within] (default = contain)
       format=json
    """

    atlas = RegulomeAtlas(regulome_es)

    region_service = RegionService(request.args, atlas)
    region_service.intercepting_regions()

    return jsonify({
        'chr': region_service.chrm,
        'start': region_service.start,
        'end': region_service.end,
        'expand': region_service.expand,
        'total_regions': region_service.total_regions,
        'regions': region_service.regions,
        'regions_per_file': region_service.regions_per_file
    })


def get_sequence(assembly, coordinate, window=50):
    if assembly == 'GRCh38':
        seq_reader = py2bit.open(TWO_BIT_HG38_FILE_PATH)
    else:
        seq_reader = py2bit.open(TWO_BIT_HG19_FILE_PATH)
    coordinate_list = coordinate.split(':')
    chrom = coordinate_list[0]
    mid = int(coordinate_list[-1].split('-')[0])
    chrom_len = seq_reader.chroms(chrom)
    start = mid - window//2
    if start >= 0:
        end = start + window
    else:
        start = 0
        end = window
    if end > chrom_len:
        end = chrom_len
        start = chrom_len - window

    sequence = {
        'chrom': chrom,
        'start': start,
        'end': end,
        'sequence': seq_reader.sequence(chrom, start, end)
    }
    seq_reader.close()
    return sequence
