from elasticsearch import helpers

from genomic_data_service.rnaseq.domain.constants import EXPRESSION_INDEX
from genomic_data_service.rnaseq.domain.constants import EXPRESSION_DOC_TYPE
from genomic_data_service.rnaseq.repository.constants import EXPRESSION_MAPPING
from genomic_data_service.rnaseq.repository.constants import MATCH_ALL


class Elasticsearch:

    INDEX = EXPRESSION_INDEX
    DOC_TYPE = EXPRESSION_DOC_TYPE
    MAPPING = EXPRESSION_MAPPING

    def __init__(self, client):
        self.es = client

    def _refresh(self):
        self.es.indices.refresh(self.INDEX)

    @property
    def data(self):
        self._refresh()
        results = self.es.search(
            index=self.INDEX,
            body=MATCH_ALL,
            size=99999,
        )
        return results.get(
            'hits',
            {}
        ).get(
            'hits',
            []
        )

    def _exists(self):
        return self.es.indices.exists(self.INDEX)

    def _maybe_create_mapping(self):
        if not self._exists():
            print('create mapping')
            self.es.indices.create(
                index=self.INDEX,
                body=self.MAPPING,
            )

    def load(self, item):
        self._maybe_create_mapping()
        self.es.index(
            index=self.INDEX,
            doc_type=self.DOC_TYPE,
            body=item,
        )

    def bulk_load(self, items):
        self._maybe_create_mapping()
        return helpers.bulk(
            self.es,
            list(items),
            chunk_size=10000,
            request_timeout=200
        )

    def bulk_load_from_files(self, files):
        self._maybe_create_mapping()
        for file_ in files:
            print('indexing', file_.props['@id'])
            self.bulk_load(
                file_.as_documents()
            )

    def clear(self):
        if self._exists():
            self.es.indices.delete(self.INDEX)
