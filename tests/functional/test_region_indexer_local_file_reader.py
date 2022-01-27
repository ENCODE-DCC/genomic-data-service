import pytest
from genomic_data_service.region_indexer_local_file_reader import LocalSnpReader

def test_local_reader():
    reader = LocalSnpReader("./tests/data/test_snp_file.bed.gz")
    assert reader.file_path == "./tests/data/test_snp_file.bed.gz"
    assert reader.file.name == './tests/data/test_snp_file.bed.gz'
    

def test_parse():
    reader = LocalSnpReader("./tests/data/test_snp_file.bed.gz")
    docs = list(reader.parse())
    assert len(docs) == 4

def test_snp():
    reader = LocalSnpReader("./tests/data/test_snp_file.bed.gz")
    docs = list(reader.parse())
    (chrom, doc) = docs[3]
    assert chrom == 'chr10'
    assert doc ==  {
        'chrom': 'chr10',
        'coordinates': {'gte': 60089, 'lt': 60090},
        'rsid': 'rs1399657112',
        'maf': 7.964e-06,
        'ref_allele_freq': {'G': {'TOPMED': 1.0}},
        'alt_allele_freq': {'T': {'TOPMED': 7.964e-06}},
    }