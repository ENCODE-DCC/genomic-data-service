from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk

RESIDENTS_INDEX = "resident_regionsets"
REGION_INDEXER_SHARDS = 2
SEARCH_MAX = 99999
FOR_REGULOME_DB = "regulomedb"

INDEX_SETTINGS = {
    "index": {
        "number_of_shards": REGION_INDEXER_SHARDS,
        "max_result_window": SEARCH_MAX,
    }
}


class RegionIndexerElasticSearch:
    def __init__(
        self,
        es_uri,
        es_port,
        supported_chroms,
        supported_assemblies,
        use_type=FOR_REGULOME_DB,
        force_delete=False,
    ):
        self.es = Elasticsearch(port=es_port, hosts=es_uri)
        self.use_type = use_type
        self.chroms = [chrom.lower() for chrom in supported_chroms]
        self.assemblies = [assembly.lower() for assembly in supported_assemblies]
        self.force_delete = force_delete

    def setup_indices(self, force_delete=False):
        if self.force_delete:
            self.destroy_indices()

        self.setup_residents_index()
        self.setup_snps_index()
        self.setup_regions_index()

    def destroy_indices(self):
        if self.es.indices.exists(RESIDENTS_INDEX):
            self.es.indices.delete(index=RESIDENTS_INDEX)

        for assembly in self.assemblies:
            snp_index = "snp_" + assembly
            if self.es.indices.exists(snp_index):
                self.es.indices.delete(index=snp_index)

        for chrom in self.chroms:
            if self.es.indices.exists(chrom):
                self.es.indices.delete(index=chrom)

    def setup_residents_index(self):
        if not self.es.indices.exists(RESIDENTS_INDEX):
            self.es.indices.create(index=RESIDENTS_INDEX, body=INDEX_SETTINGS)

        if not self.es.indices.exists_type(
            index=RESIDENTS_INDEX, doc_type=self.use_type
        ):
            mapping = self.get_resident_mapping()
            self.es.indices.put_mapping(
                index=RESIDENTS_INDEX, doc_type=self.use_type, body=mapping
            )

    def setup_snps_index(self):
        for assembly in self.assemblies:
            snp_index = "snp_" + assembly

            if not self.es.indices.exists(snp_index):
                self.es.indices.create(index=snp_index, body=INDEX_SETTINGS)

            for chrom in self.chroms:
                if not self.es.indices.exists_type(index=snp_index, doc_type=chrom):
                    mapping = self.get_snp_index_mapping(chrom)
                    self.es.indices.put_mapping(
                        index=snp_index, doc_type=chrom, body=mapping
                    )

    def setup_regions_index(self):
        for chrom in self.chroms:
            if not self.es.indices.exists(chrom):
                self.es.indices.create(index=chrom, body=INDEX_SETTINGS)

            for assembly in self.assemblies:
                if not self.es.indices.exists_type(index=chrom, doc_type=assembly):
                    mapping = self.get_chrom_index_mapping(assembly)
                    self.es.indices.put_mapping(
                        index=chrom, doc_type=assembly, body=mapping
                    )

    def get_resident_mapping(self):
        return {self.use_type: {"enabled": False}}

    def get_chrom_index_mapping(self, assembly="hg19"):
        return {
            assembly: {
                "_source": {"enabled": True},
                "properties": {
                    "uuid": {"type": "keyword"},
                    "coordinates": {"type": "integer_range"},
                    "strand": {"type": "string"},  # + - .
                    "value": {"type": "string"},
                },
            }
        }

    def get_snp_index_mapping(self, chrom="chr1"):
        return {
            chrom: {
                "_all": {"enabled": False},
                "_source": {"enabled": True},
                "properties": {
                    "rsid": {"type": "keyword"},
                    "chrom": {"type": "keyword"},
                    "coordinates": {"type": "integer_range"},
                    "maf": {
                        "type": "float",
                    },
                    "ref_allele_freq": {
                        "enabled": False,
                    },
                    "alt_allele_freq": {
                        "enabled": False,
                    },
                },
            }
        }
