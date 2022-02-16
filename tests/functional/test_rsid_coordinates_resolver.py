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


def test_ensembl_assembly_mapper():
    location = "X:1000000..1000100"
    species = "human"
    input_assembly = "GRCh37"
    output_assembly = "GRCh38"

    (chromosome, start, end) = ensembl_assembly_mapper(
        location, species, input_assembly, output_assembly
    )
    assert chromosome == "chrX"
    assert start == 1039265
    assert end == 1039365


def test_ensembl_assembly_mapper_exception():
    location = "X:1000000..1000100"
    species = "butter"
    input_assembly = "GRCh37"
    output_assembly = "GRCh38"

    (chromosome, start, end) = ensembl_assembly_mapper(
        location, species, input_assembly, output_assembly
    )
    assert chromosome == ""
    assert start == ""
    assert end == ""


def test_ensembl_assembly_mapper_no_mapping():
    location = "X:200000000..200000109"
    species = "human"
    input_assembly = "GRCh37"
    output_assembly = "GRCh38"

    (chromosome, start, end) = ensembl_assembly_mapper(
        location, species, input_assembly, output_assembly
    )
    assert chromosome == ""
    assert start == ""
    assert end == ""


def test_get_ensemblid_coordinates_grch38():
    id = "ENSG00000157764"
    assembly = "GRCh38"
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == "chr7"
    assert start == "140719327"
    assert end == "140924929"


def test_get_ensemblid_coordinates_grch37():
    id = "ENSG00000157764"
    assembly = "GRCh37"
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == "chr7"
    assert start == 140419127
    assert end == 140624729


def test_get_ensemblid_coordinates_ncbi36():
    id = "ENSG00000157764"
    assembly = "NCBI36"
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == ""
    assert start == ""
    assert end == ""


def test_get_ensemblid_coordinates_GRCm39():
    id = "ENSMUSG00000031201"
    assembly = "GRCm39"
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == "chrX"
    assert start == "74460234"
    assert end == "74497607"


def test_get_ensemblid_coordinates_GRCm38():
    id = "ENSMUSG00000031201"
    assembly = "GRCm38"
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == "chrX"
    assert start == 75416628
    assert end == 75454001


def test_get_ensemblid_coordinates_GRCm37():
    id = "ENSMUSG00000031201"
    assembly = "GRCm37"
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == "chrX"
    assert start == 72661967
    assert end == 72699340


def test_get_ensemblid_coordinates_error():
    id = "ENUSG00000157764"
    assembly = "GRCh38"
    (chromosome, start, end) = get_ensemblid_coordinates(id, assembly)
    assert chromosome == ""
    assert start == ""
    assert end == ""


def test_get_rsid_coordinates_from_ensembl_grch38():
    assembly = "GRCh38"
    rsid = "rs56116432"
    chromosome, start, end = get_rsid_coordinates_from_ensembl(assembly, rsid)
    assert chromosome == "chr9"
    assert start == 133256041
    assert end == 133256042


def test_get_rsid_coordinates_from_ensembl_grch37():
    assembly = "GRCh37"
    rsid = "rs56116432"
    chrom, start, end = get_rsid_coordinates_from_ensembl(assembly, rsid)
    assert chrom == "chr9"
    assert start == 136131428
    assert end == 136131429


def test_get_rsid_coordinates_no_atlas():
    assembly = "GRCh38"
    rsid = "rs56116432"
    chrom, start, end = get_rsid_coordinates(rsid, assembly)
    assert chrom == "chr9"
    assert start == 133256041
    assert end == 133256042


def test_get_coordinates():
    query_term = "chr10:5894499-5894500"
    chrom, start, end = get_coordinates(query_term)
    assert chrom == "chr10"
    assert start == 5894499
    assert end == 5894500


def test_get_coordinates_rsid():
    query_term = "rs56116432"
    chrom, start, end = get_coordinates(query_term)
    assert chrom == "chr9"
    assert start == 136131428
    assert end == 136131429


def test_get_coordinates_ensemblid():
    query_term = "ENSG00000157764"
    assembly = "GRCh38"
    chrom, start, end = get_coordinates(query_term, assembly)
    assert chrom == "chr7"
    assert start == 140719327
    assert end == 140924929


def test_evidence_to_features():

    evidence = {
        "ChIP": True,
        "IC_max": 1.3899999856948853,
        "PWM_matched": True,
        "Footprint_matched": True,
        "IC_matched_max": 0.05000000074505806,
        "QTL": True,
        "Footprint": True,
        "PWM": True,
        "DNase": True,
    }
    features = evidence_to_features(evidence)
    assert features["ChIP"] == True
    assert features["IC_max"] == 1.3899999856948853
    assert features["PWM_matched"] == True
    assert features["Footprint_matched"] == True
    assert features["IC_matched_max"] == 0.05000000074505806
    assert features["QTL"] == True
    assert features["Footprint"] == True
    assert features["PWM"] == True
    assert features["DNase"] == True
