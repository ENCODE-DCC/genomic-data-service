from genomic_data_service.rnaseq.domain.constants import ENSEMBL_PREFIX
from genomic_data_service.rnaseq.domain.constants import GENE_FIELDS


def get_genes_by_ensembl_id(genes):
    return dict(
        gene_by_ensembl_id
        for gene in genes
        for gene_by_ensembl_id in gene.by_ensembl_ids()
    )


class Gene:
    def __init__(self, props):
        self.props = props

    def _extract_ensembl_ids(self):
        self._ensembl_ids = [
            dbxref.replace(ENSEMBL_PREFIX, "")
            for dbxref in self.props.get("dbxrefs", [])
            if dbxref.startswith(ENSEMBL_PREFIX)
        ]

    def _extract_gene_properties(self):
        self._gene_properties = {
            k: v for k, v in self.props.items() if k in GENE_FIELDS
        }

    def by_ensembl_ids(self):
        self._extract_ensembl_ids()
        self._extract_gene_properties()
        for ensembl_id in self._ensembl_ids:
            yield (ensembl_id, self._gene_properties)
