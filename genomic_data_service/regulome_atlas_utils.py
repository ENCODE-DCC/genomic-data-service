from genomic_data_service.constants import GENOME_TO_ALIAS

def extract_search_params(params):
    assembly = params.get('genome', 'GRCh37')
    if assembly not in GENOME_TO_ALIAS.keys():
        assembly = 'GRCh37'

    from_   = params.get('from', type=int) or 0
    format  = params.get('format', 'json')
    maf     = params.get('maf', None)
    regions = params.getall('regions', [])
    size    = params.get('limit')


    region_queries = [region_query
                      for query in regions
                      for region_query in re.split(r'[\r\n]+', query)
                      if not re.match(r'^(#.*)|(\s*)$', region_query)]
    

    return assembly, from_, size, format, maf, region_queries
