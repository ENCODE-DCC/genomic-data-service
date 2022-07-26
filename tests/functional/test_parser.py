import pytest
from genomic_data_service.parser import SnfParser, RegionParser, FootPrintParser
from genomic_data_service.strand import get_matrix_array, get_pwm


def test_RegionParser_chip_seq(reader_chip_seq):
    cols_for_index = {'strand_col': 5, 'value_col': 6}
    docs = list(RegionParser(reader_chip_seq, cols_for_index).parse())
    (chrom, doc) = docs[0]
    assert chrom == 'chr5'
    assert doc == {
        'coordinates': {'gte': 150447210, 'lt': 150447494},
        'strand': '.',
        'value': '5.41785',
    }


def test_RegionParser_eqtls_grch38(reader_eqtls_grch38):
    cols_for_index = {
        'name_col': 3,
        'ensg_id_col': 8,
        'p_value_col': 14,
        'effect_size_col': 15,
    }
    docs = list(
        RegionParser(reader_eqtls_grch38, cols_for_index,
                     gene_lookup=True).parse()
    )
    (chrom, doc) = docs[0]
    assert chrom == 'chr1'
    assert doc == {
        'coordinates': {'gte': 597732, 'lt': 597733},
        'name': 'chr1_597733_A_G_b38',
        'value': 'WASH7P',
        'p_value': 6.69151e-05,
        'effect_size': '-2.27865',
        'ensg_id': 'ENSG00000227232',
    }
    (chrom, doc) = docs[3]
    assert chrom == 'chr1'
    assert doc == {
        'coordinates': {'gte': 769576, 'lt': 769577},
        'name': 'chr1_769577_G_A_b38',
        'value': 'RP11-206L10.9',
        'p_value': 1.05819e-09,
        'effect_size': '1.43971',
        'ensg_id': 'ENSG00000237491',
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


def test_foot_print_parser(reader_footprint_grch38, mocker):
    mock_reader = mocker.Mock()
    mock_reader.sequence.return_value = 'TCTGCCTGCCTTCCCTCT'
    mocker.patch('genomic_data_service.parser.py2bit.open',
                 return_value=mock_reader)
    url = 'https://www.encodeproject.org/documents/5f806098-bbf7-48e2-9ad2-588590baf2c5/@@download/attachment/MA0149.1.txt'
    matrix = get_matrix_array(url)
    pwm = get_pwm(matrix)
    docs = list(FootPrintParser(reader_footprint_grch38, pwm).parse())
    assert len(docs) == 2
    (chrom, doc) = docs[0]
    assert chrom == 'chr9'
    assert doc == {
        'coordinates': {'gte': 41229353, 'lt': 41229371},
        'strand': '-',
        'value': '5.6463',
    }


def test_foot_print_parser_with_n(reader_footprint_grch38, mocker):
    mock_reader = mocker.Mock()
    mock_reader.sequence.return_value = 'NNNNNNNNNNNNNNNNNN'
    mocker.patch('genomic_data_service.parser.py2bit.open',
                 return_value=mock_reader)
    url = 'https://www.encodeproject.org/documents/5f806098-bbf7-48e2-9ad2-588590baf2c5/@@download/attachment/MA0149.1.txt'
    matrix = get_matrix_array(url)
    pwm = get_pwm(matrix)
    docs = list(FootPrintParser(reader_footprint_grch38, pwm).parse())
    assert len(docs) == 0
