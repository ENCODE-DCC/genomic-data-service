import requests
import logging
from .constants import (
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
