from genomic_data_service import region_search_es
from genomic_data_service.rsid_coordinates_resolver import get_coordinates

REGIONS_PER_PAGE = 100
AGGREGATION_SIZE = 9999
DEFAULT_INTERVAL_MATCH = 'INTERSECTS'
INTERVAL_MATCH_OPTIONS = ['CONTAINS', 'WITHIN', 'INTERSECTS']


class RegionService():
    def __init__(self, params, atlas):
        self.assembly = params.get('assembly', 'GRCh38')

        self.query = params.get('query')

        if self.query:
            try:
                self.chrm, self.start, self.end = get_coordinates(self.query, assembly=self.assembly, atlas=atlas)
            except ValueError:
                self.chrm, self.start, self.end = (None, None, None)
        else:
            self.start = params.get('start')
            self.end = params.get('end')
            self.chrm = 'chr' + params.get('chr', '*')

        self.expand = int(params.get('expand', 0)) * 1000

        self.page = int(params.get('page', 1)) - 1
        self.limit = params.get('limit', REGIONS_PER_PAGE)
        self.files_only = params.get('files_only', '').lower() == 'true'

        self.interval = params.get('interval', DEFAULT_INTERVAL_MATCH).upper()
        if self.interval not in INTERVAL_MATCH_OPTIONS:
            self.interval = DEFAULT_INTERVAL_MATCH

        self.regions_per_file = []
        self.regions = []
        self.total_regions = 0


    def region_search_query(self):
        return {
            'query': {
                'range': {
                    'coordinates': {
                        'gte': self.start - self.expand,
                        'lte': self.end + self.expand,
                        'relation': self.interval
                    }
                }
            },
            'aggs': {
                'files': {
                    'terms': {
                        'field': 'uuid',
                        'size': AGGREGATION_SIZE,
                    }
                }
            },
            'size': (0 if self.files_only else self.limit),
            'from': self.page,
            'sort': []
        }


    def intercepting_regions(self):
        if not (self.chrm and self.start and self.end):
            return

        res = region_search_es.search(index=self.chrm, doc_type=self.assembly.lower(), _source=True, body=self.region_search_query())

        self.total_regions = res['hits']['total']

        for agg in res['aggregations']['files'].get('buckets', []):
            self.regions_per_file.append({
                'uuid': agg['key'],
                'count': agg['doc_count']
            })
        self.regions_per_file = sorted(self.regions_per_file, key=lambda k: k['count'], reverse=True)

        for r in res['hits']['hits']:
            self.regions.append({
                'chrom': r['_index'],
                'assembly': r['_type'],
                'coordinates': f"{r['_source']['coordinates']['gte']}-{r['_source']['coordinates']['lt']}",
                'value': r['_source'].get('value'),
                'strand': r['_source'].get('strand'),
                'file_url': f"https://www.encodeproject.org/{r['_source']['uuid']}"
            })
