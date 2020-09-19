import requests
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
    snp = atlas.snp(GENOME_TO_ALIAS.get(assembly), rsid)

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
        chrom, start, end = get_rsid_coordinates_from_atlas(atlas, assembly, rsid, webfetch)

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
        notifications[coord] = 'Failed: (exception) {}'.format(e)

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
