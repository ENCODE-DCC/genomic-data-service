from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk


class RegionIndexerElasticSearch():
    RESIDENTS_INDEX = 'resident_regionsets'
    REGION_INDEXER_SHARDS = 2
    SEARCH_MAX = 200
    FOR_REGULOME_DB = 'regulomedb'

    INDEX_SETTINGS = {
        "settings": {
            'index': {
                'number_of_shards': REGION_INDEXER_SHARDS,
                'max_result_window': SEARCH_MAX
            }
        }
    }

    def __init__(self, es_uri, es_port, supported_chroms, supported_assemblies, use_type=FOR_REGULOME_DB, force_delete=False):
        self.es = Elasticsearch(port=es_port, hosts=es_uri)
        self.use_type = use_type
        self.chroms = [chrom.lower() for chrom in supported_chroms]
        self.assemblies = [assembly.lower() for assembly in supported_assemblies]
        self.force_delete = force_delete

    def setup_indices(self, force_delete=False):
        if self.force_delete:
            self.destroy_indices()

        self.setup_residents_index()
        # self.setup_snps_index()
        self.setup_regions_index()

    def destroy_indices(self):
        if self.es.indices.exists(self.RESIDENTS_INDEX):
            self.es.indices.delete(index=self.RESIDENTS_INDEX)

        for assembly in self.assemblies:
            snp_index = 'snp_' + assembly
            if self.es.indices.exists(snp_index):
                self.es.indices.delete(index=snp_index)

        for assembly in self.assemblies:
            for chrom in self.chroms:
                index = get_region_index(assembly, chrom)
                if self.es.indices.exists(index):
                    self.es.indices.delete(index=index)

    def setup_residents_index(self):
        if not self.es.indices.exists(self.RESIDENTS_INDEX):
            self.es.indices.create(index=self.RESIDENTS_INDEX, body=self.INDEX_SETTINGS)

        if not self.es.indices.exists(index=self.RESIDENTS_INDEX):
            mapping = self.get_resident_mapping()
            self.es.indices.put_mapping(index=self.RESIDENTS_INDEX, body=mapping)


    def setup_snps_index(self):
        for assembly in self.assemblies:
            snp_index = 'snp_' + assembly

            if not self.es.indices.exists(snp_index):
                self.es.indices.create(index=snp_index, body=self.INDEX_SETTINGS)

            for chrom in self.chroms:
                if not self.es.indices.exists_type(index=snp_index, doc_type=chrom):
                    mapping = self.get_snp_index_mapping(chrom)
                    self.es.indices.put_mapping(index=snp_index, doc_type=chrom, body=mapping)


    def setup_regions_index(self):
        for chrom in self.chroms:
            for assembly in self.assemblies:
                index = get_region_index(assembly=assembly, chromosome=chrom)
                if not self.es.indices.exists(index=index):
                    self.es.indices.create(index=index, body=self.INDEX_SETTINGS)
                    mapping = self.get_chrom_index_mapping()
                    self.es.indices.put_mapping(index=index, body=mapping)


    def get_resident_mapping(self):
        return { "enabled": False }

    def get_chrom_index_mapping(self):
        return {
            '_source': {
                'enabled': True
            },
            'properties': {
                'uuid': {
                    'type': 'keyword'
                },
                'coordinates': {
                    'type': 'integer_range'
                },
                'strand': {
                    'type': 'keyword'  # + - .
                },
                'value': {
                    'type': 'float'
                },
            }
        }

    def get_snp_index_mapping(self, chrom='chr1'):
        return {
            chrom: {
                '_all': {
                    'enabled': False
                },
                '_source': {
                    'enabled': True
                },
                'properties': {
                    'rsid': {
                        'type': 'keyword'
                    },
                    'chrom': {
                        'type': 'keyword'
                    },
                    'coordinates': {
                        'type': 'integer_range'
                    },
                    'maf': {
                        'type': 'float',
                    },
                    'ref_allele_freq': {
                        'enabled': False,
                    },
                    'alt_allele_freq': {
                        'enabled': False,
                    },
                }
            }
        }


def get_region_index(assembly: str, chromosome: str) -> str:
    return f"{assembly.lower()}_{chromosome.lower()}"
