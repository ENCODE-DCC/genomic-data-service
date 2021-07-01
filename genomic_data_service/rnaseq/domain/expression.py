from dataclasses import dataclass


def remove_version_from_gene_id(gene_id):
    return gene_id.split('.')[0]


@dataclass
class Expression:
    gene_id: str
    transcript_ids: str
    tpm: float
    fpkm: float

    def as_dict(self):
        return {
            'gene_id': self.gene_id,
            'transcript_ids': [
                transcript_id.strip()
                for transcript_id in self.transcript_ids.split(',')
            ],
            'tpm': float(self.tpm),
            'fpkm': float(self.fpkm),
        }

    @property
    def gene_id_without_version(self):
        return remove_version_from_gene_id(
            self.gene_id
        )
