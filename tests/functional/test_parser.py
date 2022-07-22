import pytest
from genomic_data_service.parser import SnfParser, RegionParser


def test_RegionParser_chip_seq(reader_chip_seq):
    cols_for_index = {
        'strand_col': 5,
        'value_col': 6
    }
    docs = list(RegionParser(reader_chip_seq, cols_for_index).parse())
    (chrom, doc) = docs[0]
    assert chrom == 'chr5'
    assert doc == {
        'coordinates': {'gte': 150447210, 'lt': 150447494},
        'strand': '.',
        'value': '5.41785'
    }


def test_RegionParser_eqtls_grch38(reader_eqtls_grch38):
    cols_for_index = {
        'name_col': 3,
        'ensg_id_col': 8,
        'p_value_col': 14,
        'effect_size_col': 15
    }
    docs = list(RegionParser(reader_eqtls_grch38,
                cols_for_index, gene_lookup=True).parse())
    (chrom, doc) = docs[0]
    assert chrom == 'chr1'
    assert doc == {
        'coordinates': {'gte': 597732, 'lt': 597733},
        'name': 'chr1_597733_A_G_b38',
        'value': 'WASH7P',
        'p_value': 6.69151e-05,
        'effect_size': '-2.27865',
        'ensg_id': 'ENSG00000227232'
    }


def test_SnpParser(reader_snp):

    docs = list(SnfParser(reader_snp).parse())
    (chrom, doc) = docs[3]
    assert chrom == 'chr10'
    assert doc == {
        'chrom': 'chr10',
        'coordinates': {'gte': 60089, 'lt': 60090},
        'rsid': 'rs1399657112',
        'maf': 7.964e-06,
        'ref_allele_freq': {'G': {'TOPMED': 1.0}},
        'alt_allele_freq': {'T': {'TOPMED': 7.964e-06}},
    }
