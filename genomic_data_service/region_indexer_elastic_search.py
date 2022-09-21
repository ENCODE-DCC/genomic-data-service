from opensearchpy import OpenSearch


FILES_INDEX = 'files'
PEAKS_INDEX_PRE = 'peaks_'
SNPS_INDEX_PRE = 'snps_'
REGION_INDEXER_SHARDS = 2
SEARCH_MAX = 99999
SETTINGS = {
    'index': {
        'number_of_shards': REGION_INDEXER_SHARDS,
        'max_result_window': SEARCH_MAX
    }
},


auth = ('admin', 'admin')


class RegionIndexerElasticSearch():
    def __init__(self, host, port, supported_chroms, supported_assemblies, force_delete=False):
        self.opensearch = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth=auth,
            # client_cert = client_cert_path,
            # client_key = client_key_path,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            #ca_certs = ca_certs_path
        )
        self.chroms = [chrom.lower() for chrom in supported_chroms]
        self.assemblies = [assembly.lower()
                           for assembly in supported_assemblies]
        self.force_delete = force_delete

    def setup_indices(self, force_delete=False):
        if self.force_delete:
            self.destroy_indices()

        self.setup_residents_index()
        self.setup_snps_index()
        self.setup_peaks_index()

    def destroy_indices(self):
        if self.opensearch.indices.exists(FILES_INDEX):
            self.opensearch.indices.delete(index=FILES_INDEX)

        for assembly in self.assemblies:
            snp_index = SNPS_INDEX_PRE + assembly
            if self.opensearch.indices.exists(snp_index):
                self.opensearch.indices.delete(index=snp_index)
            peaks_index_pre = PEAKS_INDEX_PRE + assembly
            for chrom in self.chroms:
                peaks_index = peaks_index_pre + '_' + chrom
                if not self.opensearch.indices.exists(peaks_index):
                    self.opensearch.indices.delete(index=peaks_index)

    def setup_residents_index(self):
        if not self.opensearch.indices.exists(FILES_INDEX):
            body = self.get_files_index_body()
            print('file index body:')
            print(body)
            self.opensearch.indices.create(FILES_INDEX, body=body)

    def setup_snps_index(self):
        for assembly in self.assemblies:
            snp_index = SNPS_INDEX_PRE + assembly
            if not self.opensearch.indices.exists(snp_index):
                body = self.get_snps_index_body()
                self.opensearch.indices.create(index=snp_index, body=body)

    def setup_peaks_index(self):
        for assembly in self.assemblies:
            peaks_index_pre = PEAKS_INDEX_PRE + assembly
            for chrom in self.chroms:
                peaks_index = peaks_index_pre + '_' + chrom
                if not self.opensearch.indices.exists(peaks_index):
                    body = self.get_peaks_index_body()
                    self.opensearch.indices.create(
                        index=peaks_index, body=body)

    def get_peaks_index_body(self):
        return {
            'settings': {
                'index': {
                    'number_of_shards': REGION_INDEXER_SHARDS,
                    'max_result_window': SEARCH_MAX
                }
            },
            'mappings': {
                'properties': {
                    'uuid': {
                        'type': 'keyword'
                    },
                    'coordinates': {
                        'type': 'integer_range'
                    },
                    'strand': {
                        'type': 'text'  # + - .
                    },
                    'value': {
                        'type': 'text'
                    },
                    'name': {
                        'type': 'text'
                    },
                    'ensg_id': {
                        'type': 'text'
                    },
                    'p_value': {
                        'type': 'float'
                    },
                    'effect_size': {
                        'type': 'text'
                    }
                }
            }
        }

    def get_snps_index_body(self):
        return {
            'settings': {
                'index': {
                    'number_of_shards': REGION_INDEXER_SHARDS,
                    'max_result_window': SEARCH_MAX
                },
            },
            'mappings': {

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
                    'variation_type': {
                        'type': 'keyword'
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

    def get_files_index_body(self):
        return {
            'settings': {
                'index': {
                    'number_of_shards': REGION_INDEXER_SHARDS,
                    'max_result_window': SEARCH_MAX
                }
            }
        }
