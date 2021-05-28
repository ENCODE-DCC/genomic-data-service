from genomic_data_service import regulome_es

REGIONS_PER_PAGE = 100
AGGREGATION_SIZE = 1000
DEFAULT_INTERVAL_MATCH = 'CONTAINS'
INTERVAL_MATCH_OPTIONS = ['CONTAINS', 'WITHIN', 'INTERSECTS']


class RegionService():
    def __init__(self, params):
        self.start = params.get('start')
        self.end = params.get('end')
        self.chrm = 'chr' + params.get('chr', '*')
        self.page = int(params.get('page', 1)) - 1
        self.limit = params.get('limit', REGIONS_PER_PAGE)
        self.files_only = params.get('files_only', '').lower() == 'true'

        self.interval = params.get('interval', DEFAULT_INTERVAL_MATCH).upper()
        if self.interval not in INTERVAL_MATCH_OPTIONS:
            self.interval = DEFAULT_INTERVAL_MATCH


    def region_search_query(self):
        return {
            'query': {
                'range': {
                    'coordinates': {
                        'gte': self.start,
                        'lte': self.end,
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
        res = regulome_es.search(index=self.chrm, _source=True, body=self.region_search_query())#, size=self.limit)

        self.execution_time = res['took'] / 1000.0
        self.total_regions = res['hits']['total']

        self.regions_per_file = []
        for agg in res['aggregations']['files'].get('buckets', []):
            self.regions_per_file.append({
                'file_url': f"https://regulomedb.org/{agg['key']}",
                'count': agg['doc_count']
            })

        self.regions = []
        for r in res['hits']['hits']:
            self.regions.append({
                'chrom': r['_index'],
                'assembly': r['_type'],
                'coordinates': f"{r['_source']['coordinates']['gte']}-{r['_source']['coordinates']['lt']}",
                'value': r['_source'].get('value'),
                'strand': r['_source'].get('strand'),
                'file_url': f"https://regulomedb.org/{r['_source']['uuid']}"
            })

