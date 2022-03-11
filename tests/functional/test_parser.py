import pytest
from genomic_data_service.parser import SnfParser, RegionParser

def test_RegionParser(reader_chip_seq):

    docs = list(RegionParser(reader_chip_seq, value_col=6, strand_col=5).parse())
    (chrom, doc) = docs[0]
    assert chrom == "chr5"
    assert doc == {
        'coordinates': {'gte': 150447210, 'lt': 150447494},
        'strand': '.',
        'value': '5.41785'
    }

def test_SnpParser(reader_snp):
    
    docs = list(SnfParser(reader_snp).parse())
    (chrom, doc) = docs[3]
    assert chrom == "chr10"
    assert doc == {
        "chrom": "chr10",
        "coordinates": {"gte": 60089, "lt": 60090},
        "rsid": "rs1399657112",
        "maf": 7.964e-06,
        "ref_allele_freq": {"G": {"TOPMED": 1.0}},
        "alt_allele_freq": {"T": {"TOPMED": 7.964e-06}},
    }
