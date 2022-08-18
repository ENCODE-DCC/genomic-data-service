import pytest
from genomic_data_service.rsid_coordinates_resolver import (
    ensembl_assembly_mapper,
    get_ensemblid_coordinates,
    get_rsid_coordinates_from_ensembl,
)
from genomic_data_service.rsid_coordinates_resolver import (
    get_rsid_coordinates,
    get_coordinates,
    evidence_to_features,
)


def test_ensembl_assembly_mapper(mocker):
    location = 'X:1000000..1000100'
    species = 'human'
    input_assembly = 'GRCh37'
    output_assembly = 'GRCh38'
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'mappings': [
            {
                'mapped': {
                    'coord_system': 'chromosome',
                    'seq_region_name': 'X',
                    'assembly': 'GRCh38',
                    'end': 1039365,
                    'start': 1039265,
                    'strand': 1,
                },
                'original': {
                    'seq_region_name': 'X',
                    'coord_system': 'chromosome',
                    'strand': 1,
                    'start': 1000000,
                    'assembly': 'GRCh37',
                    'end': 1000100,
                },
            }
        ]
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response,
    )

    (chromosome, start, end) = ensembl_assembly_mapper(
        location, species, input_assembly, output_assembly
    )
    print(chromosome, start, end)
    assert chromosome == 'chrX'
    assert start == 1039265
    assert end == 1039365


def test_ensembl_assembly_mapper_exception(mocker):
    location = 'X:1000000..1000100'
    species = 'butter'
    input_assembly = 'GRCh37'
    output_assembly = 'GRCh38'

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'error': "Can not find internal name for species 'butter'"
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response,
    )

    (chromosome, start, end) = ensembl_assembly_mapper(
        location, species, input_assembly, output_assembly
    )
    assert chromosome == ''
    assert start == ''
    assert end == ''


def test_ensembl_assembly_mapper_no_mapping(mocker):
    location = 'X:200000000..200000109'
    species = 'human'
    input_assembly = 'GRCh37'
    output_assembly = 'GRCh38'

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'mappings': []
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response,
    )

    (chromosome, start, end) = ensembl_assembly_mapper(
        location, species, input_assembly, output_assembly
    )
    assert chromosome == ''
    assert start == ''
    assert end == ''


def test_get_ensemblid_coordinates_grch38(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'id': 'ENSG00000157764',
        'assembly_name': 'GRCh38',
        'description': 'B-Raf proto-oncogene, serine/threonine kinase [Source:HGNC Symbol;Acc:HGNC:1097]',
        'seq_region_name': '7',
        'source': 'ensembl_havana',
        'db_type': 'core',
        'object_type': 'Gene',
        'species': 'homo_sapiens',
        'start': 140719327,
        'logic_name': 'ensembl_havana_gene_homo_sapiens',
        'canonical_transcript': 'ENST00000646891.2',
        'end': 140924929,
        'version': 14,
        'display_name': 'BRAF',
        'biotype': 'protein_coding',
        'strand': -1,
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response,
    )
    id = 'ENSG00000157764'
    assembly = 'GRCh38'
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == 'chr7'
    assert start == '140719327'
    assert end == '140924929'


def test_get_ensemblid_coordinates_grch37(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'id': 'ENSG00000157764',
        'assembly_name': 'GRCh38',
        'description': 'B-Raf proto-oncogene, serine/threonine kinase [Source:HGNC Symbol;Acc:HGNC:1097]',
        'seq_region_name': '7',
        'source': 'ensembl_havana',
        'db_type': 'core',
        'object_type': 'Gene',
        'species': 'homo_sapiens',
        'start': 140719327,
        'logic_name': 'ensembl_havana_gene_homo_sapiens',
        'canonical_transcript': 'ENST00000646891.2',
        'end': 140924929,
        'version': 14,
        'display_name': 'BRAF',
        'biotype': 'protein_coding',
        'strand': -1,
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response
    )
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.ensembl_assembly_mapper',
        return_value=('chr7', 140419127, 140624729)
    )

    id = 'ENSG00000157764'
    assembly = 'GRCh37'
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == 'chr7'
    assert start == 140419127
    assert end == 140624729


def test_get_ensemblid_coordinates_ncbi36(mocker):
    id = 'ENSG00000157764'
    assembly = 'NCBI36'
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'id': 'ENSG00000157764',
        'assembly_name': 'GRCh38',
        'description': 'B-Raf proto-oncogene, serine/threonine kinase [Source:HGNC Symbol;Acc:HGNC:1097]',
        'seq_region_name': '7',
        'source': 'ensembl_havana',
        'db_type': 'core',
        'object_type': 'Gene',
        'species': 'homo_sapiens',
        'start': 140719327,
        'logic_name': 'ensembl_havana_gene_homo_sapiens',
        'canonical_transcript': 'ENST00000646891.2',
        'end': 140924929,
        'version': 14,
        'display_name': 'BRAF',
        'biotype': 'protein_coding',
        'strand': -1,
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response
    )
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == ''
    assert start == ''
    assert end == ''


def test_get_ensemblid_coordinates_GRCm39(mocker):
    id = 'ENSMUSG00000031201'
    assembly = 'GRCm39'
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'seq_region_name': 'X',
        'display_name': 'Brcc3',
        'strand': 1,
        'version': 18,
        'biotype': 'protein_coding',
        'id': 'ENSMUSG00000031201',
        'start': 74460234,
        'source': 'ensembl_havana',
        'db_type': 'core',
        'logic_name': 'ensembl_havana_gene_mus_musculus',
        'description': 'BRCA1/BRCA2-containing complex, subunit 3 [Source:MGI Symbol;Acc:MGI:2389572]',
        'end': 74497607,
        'species': 'mus_musculus',
        'assembly_name': 'GRCm39',
        'canonical_transcript': 'ENSMUST00000033544.14',
        'object_type': 'Gene'
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response
    )
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == 'chrX'
    assert start == '74460234'
    assert end == '74497607'


def test_get_ensemblid_coordinates_GRCm38(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'db_type': 'core',
        'species': 'mus_musculus',
        'object_type': 'Gene',
        'description': 'BRCA1/BRCA2-containing complex, subunit 3 [Source:MGI Symbol;Acc:MGI:2389572]',
        'id': 'ENSMUSG00000031201',
        'biotype': 'protein_coding',
        'seq_region_name': 'X',
        'display_name': 'Brcc3',
        'assembly_name': 'GRCm39',
        'logic_name': 'ensembl_havana_gene_mus_musculus',
        'version': 18,
        'start': 74460234,
        'source': 'ensembl_havana',
        'canonical_transcript': 'ENSMUST00000033544.14',
        'end': 74497607,
        'strand': 1
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response
    )
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.ensembl_assembly_mapper',
        return_value=('chrX', 75416628, 75454001)
    )
    id = 'ENSMUSG00000031201'
    assembly = 'GRCm38'
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == 'chrX'
    assert start == 75416628
    assert end == 75454001


def test_get_ensemblid_coordinates_GRCm37(mocker):
    id = 'ENSMUSG00000031201'
    assembly = 'GRCm37'
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'db_type': 'core',
        'species': 'mus_musculus',
        'object_type': 'Gene',
        'description': 'BRCA1/BRCA2-containing complex, subunit 3 [Source:MGI Symbol;Acc:MGI:2389572]',
        'id': 'ENSMUSG00000031201',
        'biotype': 'protein_coding',
        'seq_region_name': 'X',
        'display_name': 'Brcc3',
        'assembly_name': 'GRCm39',
        'logic_name': 'ensembl_havana_gene_mus_musculus',
        'version': 18,
        'start': 74460234,
        'source': 'ensembl_havana',
        'canonical_transcript': 'ENSMUST00000033544.14',
        'end': 74497607,
        'strand': 1
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response
    )
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.ensembl_assembly_mapper',
        return_value=('chrX', 72661967, 72699340)
    )
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == 'chrX'
    assert start == 72661967
    assert end == 72699340


def test_get_ensemblid_coordinates_error(mocker):
    id = 'ENUSG00000157764'
    assembly = 'GRCh38'
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'error': "ID 'ENUSG00000157764' not found"
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response,
    )
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == ''
    assert start == ''
    assert end == ''


def test_get_rsid_coordinates_from_ensembl_grch38(mocker):
    assembly = 'GRCh38'
    rsid = 'rs56116432'
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'var_class': 'SNP',
        'minor_allele': 'T',
        'name': 'rs56116432',
        'ambiguity': 'Y',
        'evidence': [
            'Frequency',
            '1000Genomes',
            'ESP',
            'ExAC',
            'TOPMed',
            'gnomAD'
        ],
        'mappings': [
            {
                'end': 133256042,
                'ancestral_allele': 'C',
                'strand': 1,
                'seq_region_name': '9',
                'allele_string': 'C/T',
                'assembly_name': 'GRCh38',
                'start': 133256042,
                'location': '9:133256042-133256042',
                'coord_system': 'chromosome'
            },
            {
                'assembly_name': 'GRCh38',
                'coord_system': 'chromosome',
                'start': 133256189,
                'location': 'CHR_HG2030_PATCH:133256189-133256189',
                'ancestral_allele': None,
                'end': 133256189,
                'allele_string': 'C/T',
                'strand': 1,
                'seq_region_name': 'CHR_HG2030_PATCH'
            }
        ],
        'most_severe_consequence': 'missense_variant',
        'MAF': 0.002596,
        'source': 'Variants (including SNPs and indels) imported from dbSNP',
        'synonyms': [
            'NP_065202.2:p.Gly230Asp',
            'NM_020469.3:c.689G>A',
            'NM_020469.2:c.689G>A'
        ]
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response,
    )
    chromosome, start, end = get_rsid_coordinates_from_ensembl(assembly, rsid)
    assert chromosome == 'chr9'
    assert start == 133256041
    assert end == 133256042


def test_get_rsid_coordinates_from_ensembl_grch37(mocker):
    assembly = 'GRCh37'
    rsid = 'rs56116432'
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'var_class': 'SNP',
        'minor_allele': 'T',
        'name': 'rs56116432',
        'ambiguity': 'Y',
        'evidence': [
            'Frequency',
            '1000Genomes',
            'ESP',
            'ExAC',
            'TOPMed',
            'gnomAD'
        ],
        'mappings': [
            {
                'end': 133256042,
                'ancestral_allele': 'C',
                'strand': 1,
                'seq_region_name': '9',
                'allele_string': 'C/T',
                'assembly_name': 'GRCh38',
                'start': 133256042,
                'location': '9:133256042-133256042',
                'coord_system': 'chromosome'
            },
            {
                'assembly_name': 'GRCh38',
                'coord_system': 'chromosome',
                'start': 133256189,
                'location': 'CHR_HG2030_PATCH:133256189-133256189',
                'ancestral_allele': None,
                'end': 133256189,
                'allele_string': 'C/T',
                'strand': 1,
                'seq_region_name': 'CHR_HG2030_PATCH'
            }
        ],
        'most_severe_consequence': 'missense_variant',
        'MAF': 0.002596,
        'source': 'Variants (including SNPs and indels) imported from dbSNP',
        'synonyms': [
            'NP_065202.2:p.Gly230Asp',
            'NM_020469.3:c.689G>A',
            'NM_020469.2:c.689G>A'
        ]
    }
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.requests.get',
        return_value=mock_response,
    )
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.ensembl_assembly_mapper',
        return_value=('chr9', 136131428, 136131429)
    )
    chrom, start, end = get_rsid_coordinates_from_ensembl(assembly, rsid)
    assert chrom == 'chr9'
    assert start == 136131428
    assert end == 136131429


def test_get_rsid_coordinates_no_atlas(mocker):
    assembly = 'GRCh38'
    rsid = 'rs56116432'
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.get_rsid_coordinates_from_ensembl',
        return_value=('chr9', 133256041, 133256042)
    )
    chrom, start, end = get_rsid_coordinates(rsid, assembly)
    assert chrom == 'chr9'
    assert start == 133256041
    assert end == 133256042


def test_get_coordinates():
    query_term = 'chr10:5894499-5894500'
    chrom, start, end = get_coordinates(query_term)
    assert chrom == 'chr10'
    assert start == 5894499
    assert end == 5894500


def test_get_coordinates_rsid(mocker):
    query_term = 'rs56116432'
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.get_rsid_coordinates',
        return_value=('chr9', 136131428, 136131429)
    )
    chrom, start, end = get_coordinates(query_term)
    assert chrom == 'chr9'
    assert start == 136131428
    assert end == 136131429


def test_get_coordinates_ensemblid(mocker):
    query_term = 'ENSG00000157764'
    assembly = 'GRCh38'
    mocker.patch(
        'genomic_data_service.rsid_coordinates_resolver.get_ensemblid_coordinates',
        return_value=('chr7', 140719327, 140924929)
    )
    chrom, start, end = get_coordinates(query_term, assembly)
    assert chrom == 'chr7'
    assert start == 140719327
    assert end == 140924929


def test_evidence_to_features():

    evidence = {
        'ChIP': True,
        'IC_max': 1.3899999856948853,
        'PWM_matched': True,
        'Footprint_matched': True,
        'IC_matched_max': 0.05000000074505806,
        'QTL': True,
        'Footprint': True,
        'PWM': True,
        'DNase': True,
    }
    features = evidence_to_features(evidence)
    assert features['ChIP'] == True
    assert features['IC_max'] == 1.3899999856948853
    assert features['PWM_matched'] == True
    assert features['Footprint_matched'] == True
    assert features['IC_matched_max'] == 0.05000000074505806
    assert features['QTL'] == True
    assert features['Footprint'] == True
    assert features['PWM'] == True
    assert features['DNase'] == True
