import re
import requests
import time
import logging
from genomic_data_service.constants import (
    GENOME_TO_ALIAS,
    GENOME_TO_SPECIES,
    ENSEMBL_URL,
    ENSEMBL_URL_GRCH37
)

log = logging.getLogger(__name__)

def ensembl_assembly_mapper(location, species, input_assembly, output_assembly):
    # maps location on GRCh38 to hg19 for example
    url = (ENSEMBL_URL + 'map/' + species + '/'
               + input_assembly + '/' + location + '/' + output_assembly
               + '/?content-type=application/json')
    try:
        response = requests.get(url).json()
        mappings = response["mappings"]
    except Exception:
        return('', '', '')
    
    if len(mappings) < 1:
        return('', '', '')

    data = mappings[0]['mapped']
    chromosome = 'chr' + data['seq_region_name']
    start = data['start']
    end = data['end']

    return (chromosome, start, end)


def get_rsid_coordinates_from_atlas(atlas, assembly, rsid):
    snp = atlas.find_snp(GENOME_TO_ALIAS.get(assembly), rsid)

    chrom = snp.get('chrom', None)
    coordinates = snp.get('coordinates', {})

    if chrom and coordinates and 'gte' in coordinates and 'lt' in coordinates:
        return (chrom, coordinates['gte'], coordinates['lt'])
    
    log.warning("Could not find %s on %s, using ensemble. Elasticsearch response: %s" % (rsid, assembly, snp))
    return None


def get_rsid_coordinates_from_ensembl(assembly, rsid):
    species = GENOME_TO_SPECIES.get(assembly, 'homo_sapiens')

    ensembl_url = ENSEMBL_URL_GRCH37 if (assembly == 'GRCh37') else ENSEMBL_URL

    path = "variation/%s/%s?content-type=application/json" % (species, rsid)
    url  = ensembl_url + path

    try:
        response = requests.get(url).json()
        mappings = response['mappings']
    except Exception:
        log.error("Failed connecitng to Ensembl: %s" % url)
        return('', '', '')

    for mapping in mappings:
        if 'PATCH' not in mapping['location']:
            if mapping['assembly_name'] == assembly:
                chromosome, start, end = re.split(':|-', mapping['location'])
                # must convert to 0-base
                return('chr' + chromosome, int(start) - 1, int(end))
            elif assembly == 'GRCh37':
                return ensembl_assembly_mapper(mapping['location'], species, 'GRCh38', assembly)
            elif assembly == 'GRCm37':
                return ensembl_assembly_mapper(mapping['location'], species, 'GRCm38', 'NCBIM37')

    return ('', '', '',)
    

def get_rsid_coordinates(rsid, assembly, atlas=None, webfetch=True):
    if atlas and assembly in ['GRCh38', 'hg19', 'GRCh37']:
        chrom, start, end = get_rsid_coordinates_from_atlas(atlas, assembly, rsid)

        if chrom is None and webfetch:
            raise ValueError("Could not find %s on %s, using ensemble" % (rsid, assembly))
        
        return(chrom, start, end)

    chrom, start, end = get_rsid_coordinates_from_ensembl(assembly, rsid)
    return (chrom, start, end)


def get_coordinates(query_term, assembly='GRCh37', atlas=None):
    query_term = query_term.lower()

    chrom, start, end = None, None, None

    query_match = re.match(
        r'^(chr[1-9]|chr1[0-9]|chr2[0-2]|chrx|chry)(?:\s+|:)(\d+)(?:\s+|-)(\d+)',
        query_term
    )

    if query_match:
        chrom, start, end = query_match.groups()
    else:
        query_match = re.match(r'^rs\d+', query_term)
        if query_match:
            chrom, start, end = get_rsid_coordinates(query_match.group(0),
                                                     assembly, atlas)
    try:
        start, end = int(start), int(end)
    except (ValueError, TypeError):
        raise ValueError('Region "{}" is not recognizable.'.format(query_term))

    chrom = chrom.replace('x', 'X').replace('y', 'Y')

    return chrom, min(start, end), max(start,end)


def resolve_coordinates_and_variants(region_queries, assembly, atlas, maf):
    variants          = {}
    notifications     = {}
    query_coordinates = []

    for region_query in region_queries:
        try:
            chrom, start, end = get_coordinates(region_query, assembly, atlas)
        except ValueError:
            notifications[region_query] = 'Failed: invalid region input'
            continue

        query_coordinates.append('{}:{}-{}'.format(chrom, int(start), int(end)))

        snps = atlas.find_snps(
            GENOME_TO_ALIAS.get(assembly, 'hg19'), chrom, start, end, maf=maf
        )

        if re.match(r'^rs\d+', region_query.lower()):
            snps.append(
                {
                    'rsid': region_query.lower(),
                    'chrom': chrom,
                    'coordinates': {
                        'gte': start,
                        'lt': end,
                    }
                }
            )

        if not snps:
            if (int(end) - int(start)) > 1:
                notifications[region_query] = (
                    'Failed: no known variants matching query conditions found.'
                )
                continue
            else:
                variants[(chrom, int(start), int(end))] = set()

        for snp in snps:
            coord = (
                snp['chrom'],
                snp['coordinates']['gte'],
                snp['coordinates']['lt']
            )
            if coord in variants:
                variants[coord].add(snp['rsid'])
            else:
                variants[coord] = {snp['rsid']}

    return (variants, query_coordinates, notifications)


def region_get_hits(atlas, assembly, chrom, start, end, peaks_too=False):
    '''Returns a list of file uuids AND dataset paths for chromosome location'''

    all_hits = {}

    (peaks, peak_details) = atlas.find_peaks_filtered(GENOME_TO_ALIAS[assembly], chrom, start, end,
                                                      peaks_too)
    if not peaks:
        return {'message': 'No hits found in this location'}
    if peak_details is None:
        return {'message': 'Error during peak filtering'}
    if not peak_details:
        return {'message': 'No %s sources found' % atlas.type()}

    all_hits['peak_count'] = len(peaks)
    if peaks_too:
        all_hits['peaks'] = peaks  # For "download_elements", contains 'inner_hits' with positions
    # NOTE: peak['inner_hits']['positions']['hits']['hits'] may exist with uuids but to same file

    (all_hits['datasets'], all_hits['files']) = atlas.details_breakdown(peak_details)

    all_hits['dataset_paths'] = list(all_hits['datasets'].keys())
    all_hits['file_count'] = len(all_hits['files'])
    all_hits['dataset_count'] = len(all_hits['datasets'])
    all_hits['message'] = ('%d peaks in %d files belonging to %s datasets in this region' %
                           (all_hits['peak_count'], all_hits['file_count'],
                            all_hits['dataset_count']))

    return all_hits


# TODO: refactor
def evidence_to_features(evidence):
    features = {
        'ChIP': False,
        'DNase': False,
        'PWM': False,
        'Footprint': False,
        'QTL': False,
        'PWM_matched': False,
        'Footprint_matched': False,
        'IC_matched_max': 0.0,
        'IC_max': 0.0,
    }

    for k in features:
        if isinstance(features[k], float):
            features[k] = evidence.get(k, 0.0)
        else:
            features[k] = k in evidence

    return features


def search_peaks(query_coordinates, atlas, assembly, num_variants):
    coord = query_coordinates[0]
    chrom, start_end = coord.split(':')
    start, end = start_end.split('-')
    start = int(start)
    end = int(end)

    features = None
    regulome_score = None
    notifications = {}
    peak_details = []
    all_hits = []
    graph = None
    timing = []

    begin = time.time()

    try:
        all_hits = region_get_hits(
            atlas, assembly, chrom, start, end, peaks_too=True
        )
        evidence = atlas.regulome_evidence(
            all_hits['datasets'], chrom, start, end
        )
        regulome_score = atlas.regulome_score(
            all_hits['datasets'], evidence
        )
        features = evidence_to_features(evidence)
    except Exception as e:
        all_hits = {}
        notifications[coord] = 'Failed: (exception) {}'.format(e)

    for peak in all_hits.get('peaks', []):
        documents =[resolve_relative_hrefs(document, 'document') for document in peak['resident_detail']['dataset']['documents']]

        peak_details.append({
            'chrom': peak['_index'],
            'start': peak['_source']['coordinates']['gte'],
            'end': peak['_source']['coordinates']['lt'],
            'strand': peak['_source'].get('strand'),
            'value': peak['_source'].get('value'),
            'file': peak['resident_detail']['file']['@id'].split('/')[2],
            'targets': peak['resident_detail']['dataset'].get('target', []),
            'method': peak['resident_detail']['dataset']['collection_type'],

            'documents': documents,
            'dataset': resolve_relative_hrefs(peak['resident_detail']['dataset']['@id'], 'dataset'),
            'dataset_rel': peak['resident_detail']['dataset']['@id'],
            'biosample_ontology': resolve_relative_hrefs(peak['resident_detail']['dataset']['biosample_ontology'], 'biosample_ontology'),
        })

    graph = peak_details

    timing.append({'regulome_search_scoring': (time.time() - begin)})

    begin = time.time()
    nearby_snps = atlas.nearby_snps(
        GENOME_TO_ALIAS.get(assembly, 'hg19'),
        chrom,
        int((start + end) / 2),
        # No guarentee the query coordinate corresponds to one RefSNP.
        max_snps=num_variants+10
    )
    timing.append({'nearby_snps': (time.time() - begin)})

    return (regulome_score, features, notifications, graph, timing, nearby_snps)


def resolve_relative_hrefs(obj, obj_type=''):
    path = 'https://www.encodeproject.org'

    if not obj:
        return obj

    if obj_type == 'dataset':
        return path + obj

    if obj_type == 'document':
        encode_id = obj['@id']
        if obj['aliases']:
            encode_id = f"/{obj['aliases'][0]}/"

        obj['@id'] = path + encode_id

        for field in ['award', 'lab', 'submitted_by']:
            if field in obj and type(obj[field]) is dict:
                obj[field] = path + obj[field].get('@id', '')

        return obj

    if obj_type == 'biosample_ontology':
        obj['@id'] = path + obj['@id']
        return obj


def score_regions(variants, es, atlas, assembly):
    if result['format'] in ['tsv', 'bed']:
        table = []

    timings = []
        
    for variant in result['variants']:
        begin = time.time()
        chrom = variant['chrom']
        start = variant['start']
        end = variant['end']
        # parse_region_query makes sure variants returned are all scorable

        try:
            all_hits = region_get_hits(atlas, assembly, chrom, start, end)
            evidence = atlas.regulome_evidence(all_hits['datasets'], chrom, int(start), int(end))
            regulome_score = atlas.regulome_score(all_hits['datasets'], evidence)
            features = evidence_to_features(evidence)
        except Exception as e:
            features = {}
            regulome_score = {}
            raise e # testing

        if result['format'] in ['tsv', 'bed']:
            if not table:
                columns = ['chrom', 'start', 'end', 'rsids']
                columns.extend(sorted(regulome_score.keys()))
                columns.extend(sorted(features.keys()))
                if result['format'] == 'tsv':
                    table.append('\t'.join(columns).encode())
            row = [chrom, start, end, ', '.join(variant['rsids'])]
            row.extend([
                str(features.get(col, '')) or str(regulome_score.get(col, ''))
                for col in columns
                if col in regulome_score or col in features
            ])
            table.append('\t'.join(row).encode())
            continue
        else:
            variant['features'] = features
            variant['regulome_score'] = regulome_score
        timings.append(
            {'{}:{}-{}'.format(chrom, start, end): (time.time() - begin)}
        )

