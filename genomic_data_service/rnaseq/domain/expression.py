from dataclasses import dataclass


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
