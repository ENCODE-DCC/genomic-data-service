from pymongo import MongoClient
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
        self.mongo = MongoClient()
        self.use_type = use_type
        self.chroms = [chrom.lower() for chrom in supported_chroms]
        self.assemblies = [assembly.lower() for assembly in supported_assemblies]
        self.force_delete = force_delete

    def setup_indices(self, force_delete=False):
        db = self.mongo.gds
        cols = [
            "hg19_chr21",
            "hg19_chr10",
            "hg19_chr16",
            "hg19_chr1",
            "hg19_chr2",
            "hg19_chr17",
            "hg19_chr5",
            "hg19_chrX",
            "hg19_chr12",
            "hg19_chr19",
            "hg19_chr6",
            "hg19_chr13",
            "hg19_chr18",
            "hg19_chr4",
            "hg19_chr11",
            "hg19_chr14",
            "hg19_chr3",
            "hg19_chrY",
            "hg19_chr7",
            "hg19_chr20",
            "hg19_chr9",
            "hg19_chr8",
            "hg19_chr15",
            "hg19_chr22",
            "GRCh38_chr2",
            "GRCh38_chr18",
            "GRCh38_chr22",
            "GRCh38_chr5",
            "GRCh38_chr17",
            "GRCh38_chr3",
            "GRCh38_chr8",
            "GRCh38_chr19",
            "GRCh38_chrX",
            "GRCh38_chr1",
            "GRCh38_chr9",
            "GRCh38_chr21",
            "GRCh38_chr7",
            "GRCh38_chr15",
            "GRCh38_chr4",
            "GRCh38_chr11",
            "GRCh38_chr14",
            "GRCh38_chr13",
            "GRCh38_chrY",
            "GRCh38_chr16",
            "GRCh38_chr12",
            "GRCh38_chr6",
            "GRCh38_chr20",
            "GRCh38_chr10",
        ]
        snps_cols = ["snp_hg19",]
        for col in cols:
            resp = db[col].create_index(
                [
                    ("coordinates.gte", 1),
                    ("coordinates.lt", 1),
                ]
            )

            print("index response:", resp)
