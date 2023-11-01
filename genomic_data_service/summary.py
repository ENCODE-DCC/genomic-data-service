import time
from flask import jsonify, request, redirect, url_for, make_response
from werkzeug.exceptions import BadRequest
from genomic_data_service import regulome_es, app
from genomic_data_service.regulome_atlas import RegulomeAtlas
from genomic_data_service.rsid_coordinates_resolver import resolve_coordinates_and_variants, region_get_hits, evidence_to_features
from genomic_data_service.request_utils import validate_search_request, extract_search_params
from genomic_data_service.constants import REGULOME_VALID_ASSEMBLY


def build_response(block):
    return {
        **block, **{
            '@context': '/terms/',
            '@id': request.full_path,
            '@type': ['summary'],
            'title': 'Genomic Summary'
        }
    }


def build_download(table, format_):
    response = make_response('\n'.join(table))
    response.headers['Content-Type'] = 'text/tsv'
    response.headers['Content-Disposition'] = 'attachment;filename="regulome_{}.{}"'.format(
        time.strftime('%Y%m%d-%Hh%Mm%Ss'), format_
    )
    return response


def build_redirect_to_search(variants, assembly):
    regions = [
        '{}:{}-{}'.format(v['chrom'], v['start'], v['end'])
        for v in variants
    ][0]

    return redirect(url_for('search', genome=assembly, regions=regions), code=302)


@app.route('/summary/', methods=['GET', 'POST'])
def summary():
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

    atlas = RegulomeAtlas(regulome_es)

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
        'format': format_.lower(),
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

    if not result['variants']:
        if not result['notifications']:
            result['notifications'] = {'Failed': 'No variants found'}
        return jsonify(build_response(result))

    if len(result['variants']) == 1 and not result['notifications']:
        return build_redirect_to_search(result['variants'], result['assembly'])

    table_download = format_ in ['tsv', 'bed']
    table = []

    for variant in result['variants']:
        begin = time.time()

        chrom = variant['chrom']
        start = variant['start']
        end = variant['end']

        all_hits = region_get_hits(atlas, assembly, chrom, start, end)
        datasets = all_hits.get('datasets', [])
        evidence = atlas.regulome_evidence(
            assembly, datasets, chrom, int(start), int(end))
        regulome_score = atlas.regulome_score(datasets, evidence)
        features = evidence_to_features(evidence)

        if table_download:
            if not table:
                columns = ['chrom', 'start', 'end', 'rsids']
                columns.extend(sorted(regulome_score.keys()))
                columns.extend(sorted(features.keys()))
                if format_ == 'tsv':
                    table.append('\t'.join(columns))
            row = [chrom, start, end, ', '.join(variant['rsids'])]
            row.extend([
                str(features.get(col, '')) or str(regulome_score.get(col, ''))
                for col in columns
                if col in regulome_score or col in features
            ])

            string_row = [str(r) for r in row]
            table.append('\t'.join(string_row))
            continue

        variant['features'] = features
        variant['regulome_score'] = regulome_score

        result['timing'].append(
            {'{}:{}-{}'.format(chrom, start, end): (time.time() - begin)}
        )

    if table_download:
        return build_download(table, format_)

    return jsonify(build_response(result))
