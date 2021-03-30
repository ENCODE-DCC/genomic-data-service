from genomic_data_service.models import Gene

AUTOCOMPLETE_INDEX = 'rna_seq_autocomplete'
AUTOCOMPLETE_PAGE_SIZE = 30

class RNASeqES():
    def __init__(self, es):
        self.es = es


    def setup_index(self, delete=False):
        INDEX_SETTINGS = {
            'index': {
                'max_result_window': 200
            }
        }

        if delete:
            self.es.indices.delete(index=AUTOCOMPLETE_INDEX)

        if not self.es.indices.exists(AUTOCOMPLETE_INDEX):
            self.es.indices.create(index=AUTOCOMPLETE_INDEX, body=INDEX_SETTINGS)


    def create_mapping(self):
        mapping = {
            'genes': {
                'properties': {
                    'name': {
                        'type': 'completion'
                    }
                }
            }
        }

        self.es.indices.put_mapping(index=AUTOCOMPLETE_INDEX, doc_type='genes', body=mapping)


    def index_genes(self):
        genes = Gene.query.with_entities(Gene.id, Gene.symbol, Gene.encode_id).all()

        for gene in genes:
            data = {
                'name': {
                    'input': [gene.id.upper(), gene.symbol.upper()]
                }
            }

            self.es.index(index=AUTOCOMPLETE_INDEX, doc_type='genes', body=data, id=gene.encode_id)


    def autocomplete_genes(self, text):
        query = {
            'suggest': {
                'gene-suggest': {
                    'prefix': text.upper(),
                    'completion': {
                        'field': 'name',
                        'size': AUTOCOMPLETE_PAGE_SIZE
                    }
                }
            }
        }

        results = self.es.search(index=AUTOCOMPLETE_INDEX, doc_type='genes', body=query)

        if results['suggest']['gene-suggest'][0]['length'] == 0:
            return []

        options = sorted(results['suggest']['gene-suggest'][0]['options'], key = lambda i: i['_score'], reverse=True)

        return [option['text'] for option in options]


if __name__ == '__main__':
    from genomic_data_service import es

    indexer = RNASeqES(es)
    
    indexer.setup_index(delete=True)
    indexer.create_mapping()
    indexer.index_genes()

