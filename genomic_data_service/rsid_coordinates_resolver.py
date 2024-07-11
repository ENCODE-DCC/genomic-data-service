import re
import requests
import time
import logging
from genomic_data_service.constants import (
    CATALOG_API_FREQ,
    CATALOG_API_VARIANTS,
    CHR_GRCH37,
    CHR_GRCH38,
    GENOME_TO_ALIAS,
    GENOME_TO_SPECIES,
    ENSEMBL_URL,
    ENSEMBL_URL_GRCH37
)

log = logging.getLogger(__name__)


def get_variants_from_catalog(region_queries, source='bravo_af', maf=0.01):
    """
    This function use catalog api to query SNPs for give region querys.
    :param region_queries: list of region queries
    :param source: source of the variants frequency
    :param maf: minimum allele frequency
    :return: a list of variants sorted by chrom, start position, ref and alt.
    there are two APIs to use.
    If the query is coordiantes, it is more than one base long, we use variantByFrequencySource endpoint.
    The source and maf have default values, but can be changed by user input.
    Otherwise, we use variants endpoint.
    Those two endpoints return all types of variants, so we need to filter for only SNPs.
    The max limit for the two endpoints is 500.
    Notification need to be added when:
    1. the region query is not in the valid format(only coordinates, rsid, spdi and hgvs is allowed).
    2. the start and end are the same.
    3. no known variants matching query coordinates found.
    If the coordinates is one base long, even though no viariants are found, it will not generate notification.
    Instead, we will still add this coordinates to variants list.
    """
    region_queries = list(set(region_queries))
    notifications = {}
    query_coordinates = []
    variants = []
    api_base = CATALOG_API_VARIANTS
    api = ''
    for region_query in region_queries:
        is_single_base = False
        # example of region_query: chr1:10000-10001
        if re.match(r'^(chr[1-9]|chr1[0-9]|chr2[0-2]|chrx|chry)(?:\s+|:)(\d+)(?:\s+|-)(\d+)$', region_query):
            chrom = region_query.split(':')[0]
            start_end = region_query.split(':')[-1].split('-')
            start = int(start_end[0])
            end = int(start_end[1])
            if end - start <= 0:
                notifications[region_query] = (
                    'Failed: coordinates start should be smaller than coordinates end.'
                )
                continue
            if end - start > 1:
                api_base = CATALOG_API_FREQ
                api = f'{api_base}&region={region_query}&source={source}&minimum_af={maf}'
            else:
                is_single_base = True
                api = api_base + '&region={}'.format(region_query)

        # example of region_query: rs4970774
        elif re.match(r'^rs\d+$', region_query):
            api = api_base + '&rsid={}'.format(region_query)
        # example of region_query: NC_000001.11:109726205:A:T
        elif re.match(r'^NC_\d{6}\.\d{1,2}:\d+:\w:\w$', region_query):
            api = api_base + '&spdi={}'.format(region_query)
        # example of region_query: NC_000001.11:g.109726206A>T
        elif re.match(r'^NC_\d{6}\.\d{1,2}:g\.\d+\w>\w$', region_query):
            api = api_base + '&hgvs={}'.format(region_query)
        else:
            notifications[region_query] = 'Failed: invalid region input'
            continue
        logging.info(f'api: {api}')
        res = requests.get(api).json()
        res = [variant for variant in res if len(
            variant['ref']) == 1 and len(variant['alt']) == 1]
        if res:
            for variant in res:
                freq = variant['annotations'].copy()
                if freq.get('GENCODE_category'):
                    del freq['GENCODE_category']
                variants.append({
                    'chrom': variant['chr'],
                    'start': variant['pos'],
                    'end': variant['pos'] + 1,
                    'rsids': variant['rsid'],
                    'ref': variant['ref'],
                    'alt': variant['alt'],
                    'hgvs': variant['hgvs'],
                    'spdi': variant['spdi'],
                    'gencode_category': variant['annotations'].get('GENCODE_category'),
                    'freq': freq,
                })
                query_coordinates.append(
                    '{}:{}-{}'.format(variant['chr'], variant['pos'], variant['pos'] + 1))
        else:
            if is_single_base:
                variants.append({
                    'chrom': chrom,
                    'start': start,
                    'end': end,
                    'rsids': list(),
                    'ref': list(),
                    'alt': list(),
                    'hgvs': None,
                    'spdi': None,
                    'gencode_category': None,
                    'freq': {}
                })
                query_coordinates.append(region_query)
            else:
                notifications[region_query] = f'Failed: no known SNPs matching {region_query} found.'

    variants = sorted(variants, key=lambda variant: (
        variant['chrom'], variant['start'], variant['ref'], variant['alt']))
    return (variants, list(set(query_coordinates)), notifications)


def ensembl_assembly_mapper(location, species, input_assembly, output_assembly):
    # maps location on GRCh38 to hg19 for example
    url = (ENSEMBL_URL + 'map/' + species + '/'
           + input_assembly + '/' + location + '/' + output_assembly
           + '/?content-type=application/json')
    try:
        response = requests.get(url).json()
        mappings = response['mappings']
    except Exception:
        return('', '', '')

    if len(mappings) < 1:
        return('', '', '')

    data = mappings[0]['mapped']
    chromosome = 'chr' + data['seq_region_name']
    start = data['start']
    end = data['end']

    return (chromosome, start, end)


def get_ensemblid_coordinates(id, assembly):
    species = GENOME_TO_SPECIES.get(assembly, 'homo_sapiens')
    url = '{ensembl}lookup/id/{id}?content-type=application/json'.format(
        ensembl=ENSEMBL_URL,
        id=id
    )
    try:
        response = requests.get(url).json()
    except:
        return('', '', '')
    else:
        if 'error' in response:
            return ('', '', '')

        location = '{chr}:{start}-{end}'.format(
            chr=response['seq_region_name'],
            start=response['start'],
            end=response['end']
        )
        if response['assembly_name'] == assembly:
            chromosome, start, end = re.split(':|-', location)
            return('chr' + chromosome, start, end)
        elif assembly == 'GRCh37':
            return ensembl_assembly_mapper(location, species, 'GRCh38', assembly)
        elif assembly == 'GRCm38':
            return ensembl_assembly_mapper(location, species, 'GRCm39', assembly)
        elif assembly == 'GRCm37':
            return ensembl_assembly_mapper(location, species, 'GRCm39', 'NCBIM37')
        else:
            return ('', '', '')


def get_rsid_coordinates_from_atlas(atlas, assembly, rsid):
    snp = atlas.find_snp(GENOME_TO_ALIAS.get(assembly), rsid)
    if snp:
        chrom = snp.get('chrom', None)
        coordinates = snp.get('coordinates', {})

        if chrom and coordinates and 'gte' in coordinates and 'lt' in coordinates:
            return (chrom, coordinates['gte'], coordinates['lt'])

    log.warning('Could not find %s on %s, using ensemble. Elasticsearch response: %s' % (
        rsid, assembly, snp))
    return (None, None, None)


def get_rsid_coordinates_from_ensembl(assembly, rsid):
    species = GENOME_TO_SPECIES.get(assembly, 'homo_sapiens')

    ensembl_url = ENSEMBL_URL_GRCH37 if (assembly == 'GRCh37') else ENSEMBL_URL

    path = 'variation/%s/%s?content-type=application/json' % (species, rsid)
    url = ensembl_url + path

    try:
        response = requests.get(url).json()
        mappings = response['mappings']
    except Exception:
        log.error('Failed connecitng to Ensembl: %s' % url)
        return('', '', '')

    for mapping in mappings:
        if 'PATCH' not in mapping['location']:
            if mapping['assembly_name'] == assembly:
                chromosome, start, end = re.split(':|-', mapping['location'])
                # must convert to 0-base
                return('chr' + chromosome, int(start) - 1, int(end))
            elif assembly == 'GRCh37':
                return ensembl_assembly_mapper(mapping['location'], species, 'GRCh38', assembly)
    return ('', '', '',)


def get_rsid_coordinates(rsid, assembly, atlas=None, webfetch=True):
    if atlas and assembly in ['GRCh38', 'hg19', 'GRCh37']:
        chrom, start, end = get_rsid_coordinates_from_atlas(
            atlas, assembly, rsid)

        if chrom is None and webfetch:
            raise ValueError(
                'Could not find %s on %s, using ensemble' % (rsid, assembly))

        return(chrom, start, end)

    chrom, start, end = get_rsid_coordinates_from_ensembl(assembly, rsid)
    return (chrom, start, end)


def get_chrom_from_chrom_ref(chrom_ref):
    chr_num = int(chrom_ref.split('.')[0].split('_')[-1])
    if chr_num == 23:
        chr_num = 'X'
    elif chr_num == 24:
        chr_num = 'Y'
    chrom = 'chr' + str(chr_num)
    return chrom


def get_spdi_coordinates(chrom_ref, spdi_suffix):
    chrom = get_chrom_from_chrom_ref(chrom_ref)
    start = int(spdi_suffix.split(':')[0])
    end = start + 1
    return (chrom, start, end)


def get_hgvs_coordinates(chrom_ref, hgvs_suffix):
    chrom = get_chrom_from_chrom_ref(chrom_ref)
    start = int(hgvs_suffix[2: len(hgvs_suffix)-3]) - 1
    end = start + 1
    return (chrom, start, end)


def get_coordinates(query_term, assembly='GRCh37', atlas=None):
    query_term = query_term.lower()

    chrom, start, end = None, None, None

    query_match = re.match(
        r'^(chr[1-9]|chr1[0-9]|chr2[0-2]|chrx|chry)(?:\s+|:)(\d+)(?:\s+|-)(\d+)$',
        query_term
    )

    if query_match:
        chrom, start, end = query_match.groups()
    else:
        query_match = re.match(r'^rs\d+$', query_term)
        if query_match:
            chrom, start, end = get_rsid_coordinates(query_match.group(0),
                                                     assembly, atlas)
        else:
            query_match = re.match(r'^ensg\d+$', query_term)
            if query_match:
                chrom, start, end = get_ensemblid_coordinates(
                    query_term.upper(), assembly)
            else:
                tokens = query_term.split(':', 1)
                if (assembly == 'GRCh38' and tokens[0] in CHR_GRCH38) or (assembly in ['GRCh37', 'hg19'] and tokens[0] in CHR_GRCH37):
                    query_match = re.match(
                        r'^[0-9]+:(a|c|g|t|u|r|y|k|m|s|w|b|d|h|v|n):(a|c|g|t|u|r|y|k|m|s|w|b|d|h|v|n)', tokens[-1])
                    if query_match:
                        chrom, start, end = get_spdi_coordinates(
                            tokens[0], tokens[1])
                    else:
                        query_match = re.match(
                            r'^g.[0-9]+(a|c|g|t|u|r|y|k|m|s|w|b|d|h|v|n)>(a|c|g|t|u|r|y|k|m|s|w|b|d|h|v|n)', tokens[-1])
                        if query_match:
                            chrom, start, end = get_hgvs_coordinates(
                                tokens[0], tokens[1])
    if type(start) != int and type(end) != int:
        try:
            start, end = int(start), int(end)
        except (ValueError, TypeError):
            raise ValueError(
                'Region "{}" is not recognizable.'.format(query_term))

    chrom = chrom.replace('x', 'X').replace('y', 'Y')

    return chrom, min(start, end), max(start, end)


def resolve_coordinates_and_variants(region_queries, assembly, atlas, maf):
    variants = {}
    notifications = {}
    query_coordinates = []
    for region_query in region_queries:
        try:
            chrom, start, end = get_coordinates(region_query, assembly, atlas)
        except:
            notifications[region_query] = 'Failed: invalid region input'
            continue
        if start == end:
            notifications[region_query] = (
                'Failed: coordinates start and end can not be the same.'
            )
            continue

        query_coordinates.append(
            '{}:{}-{}'.format(chrom, int(start), int(end)))
        # if the region is only one base long, we ignore maf score.
        if (int(end) - int(start)) == 1:
            maf = None
        snps = atlas.find_snps(
            GENOME_TO_ALIAS.get(assembly, 'hg19'), chrom, start, end, maf=maf
        )

        if not snps:
            if (int(end) - int(start)) > 1:
                notifications[region_query] = (
                    'Failed: no known variants matching query conditions found.'
                )
                continue
            else:
                # we keep the region in the variant as long as it is only one base long, even no snps returned.
                variants[(chrom, int(start), int(end))] = {
                    'rsids': set(),
                }

        for snp in snps:
            coord = (
                snp['chrom'],
                snp['coordinates']['gte'],
                snp['coordinates']['lt']
            )
            if coord in variants:
                variants[coord]['rsids'].add(snp['rsid'])
            else:
                variants[coord] = {}
                variants[coord]['rsids'] = {snp['rsid']}
            if snp.get('variation_type') == 'SNV':
                variants[coord]['ref'] = list(snp['ref_allele_freq'].keys())
                variants[coord]['alt'] = list(snp['alt_allele_freq'].keys())
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
        # For "download_elements", contains 'inner_hits' with positions
        all_hits['peaks'] = peaks
    # NOTE: peak['inner_hits']['positions']['hits']['hits'] may exist with uuids but to same file

    (all_hits['datasets'], all_hits['files']
     ) = atlas.details_breakdown(peak_details)

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
        'Chromatin_accessibility': False,
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
        datasets = all_hits.get('datasets', [])
        evidence = atlas.regulome_evidence(
            assembly, datasets, chrom, start, end
        )
        regulome_score = atlas.regulome_score(
            datasets, evidence
        )
        features = evidence_to_features(evidence)
    except Exception as e:
        all_hits = {}
        notifications[coord] = 'Failed: (exception) {}'.format(e)

    for peak in all_hits.get('peaks', []):
        documents = [resolve_relative_hrefs(
            document, 'document') for document in peak['resident_detail']['dataset']['documents']]
        peak_detail = {
            'chrom': peak['_index'],
            'start': peak['_source']['coordinates']['gte'],
            'end': peak['_source']['coordinates']['lt'],
            'strand': peak['_source'].get('strand'),
            'value': peak['_source'].get('value'),
            'file': peak['resident_detail']['file']['@id'].split('/')[2],
            'targets': peak['resident_detail']['dataset'].get('target', []),
            'target_label': peak['resident_detail']['dataset'].get('target_label'),
            'disease_term_name': peak['resident_detail']['dataset'].get('disease_term_name'),
            'method': peak['resident_detail']['dataset']['collection_type'],
            'ancestry': peak['resident_detail']['file'].get('ancestry'),
            'files_for_genome_browser': peak['resident_detail']['dataset'].get('files_for_genome_browser', []),
            'documents': documents,
            'dataset': resolve_relative_hrefs(peak['resident_detail']['dataset']['@id'], 'dataset'),
            'dataset_rel': peak['resident_detail']['dataset']['@id'],
            'biosample_ontology': resolve_relative_hrefs(peak['resident_detail']['dataset']['biosample_ontology'], 'biosample_ontology'),
        }
        if peak_detail['method'] == 'footprints':
            peak_detail['footprint_assay_term_name'] = peak['resident_detail']['dataset']['footprint_assay_term_name']
        peak_details.append(peak_detail)

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
