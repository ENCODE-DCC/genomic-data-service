import requests

from genomic_data_service.rnaseq.domain.constants import GENES
from genomic_data_service.rnaseq.domain.constants import DATASETS
from genomic_data_service.rnaseq.domain.file import RnaSeqFile
from genomic_data_service.rnaseq.domain.gene import get_genes_by_ensembl_id
from genomic_data_service.rnaseq.domain.gene import Gene

from genomic_data_service.rnaseq.remote.constants import AT_GRAPH
from genomic_data_service.rnaseq.remote.constants import BASE_URL
from genomic_data_service.rnaseq.remote.constants import FILE_PARAMS
from genomic_data_service.rnaseq.remote.constants import DATASET_PARAMS
from genomic_data_service.rnaseq.remote.constants import GENE_PARAMS
from genomic_data_service.rnaseq.remote.constants import SEARCH_PATH


def get_json(url):
    response = requests.get(url)
    return response.json()


class Portal:

    BASE_URL = BASE_URL

    def __init__(self):
        self.repositories = {}

    def _get_gene_url(self):
        return self.BASE_URL + SEARCH_PATH + GENE_PARAMS

    def load_genes(self):
        print('loadinig genes')
        url = self._get_gene_url()
        genes = (
            Gene(props)
            for props in get_json(url)[AT_GRAPH]
        )
        self.repositories[GENES] = get_genes_by_ensembl_id(
            genes
        )

    def _get_dataset_url(self):
        return self.BASE_URL + SEARCH_PATH + DATASET_PARAMS

    def load_datasets(self):
        print('loading datasets')
        url = self._get_dataset_url()
        self.repositories[DATASETS] = {
            dataset['@id']: dataset
            for dataset in get_json(url)[AT_GRAPH]
        }

    def _get_file_url(self):
        return self.BASE_URL + SEARCH_PATH + FILE_PARAMS

    def get_rna_seq_files(self):
        print('getting files')
        self.load_genes()
        self.load_datasets()
        url = self._get_file_url()
        return (
            RnaSeqFile(props, self.repositories)
            for props in get_json(url)[AT_GRAPH]
        )
