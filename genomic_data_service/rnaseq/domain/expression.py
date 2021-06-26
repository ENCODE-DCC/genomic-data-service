from dataclasses import dataclass


@dataclass
class Expression:
    gene_id: str
    transcript_ids: str
    tpm: float
    fpkm: float
