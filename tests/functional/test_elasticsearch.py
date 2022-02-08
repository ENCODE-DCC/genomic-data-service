import pytest

from genomic_data_service.region_indexer import dataset_accession


def test_indices(regulome_elasticsearch_client):
    regulome_elasticsearch_client.setup_indices()
    indices = list(regulome_elasticsearch_client.es.indices.get_alias().keys())
    indices.sort()
    assert indices == [
        "chr1",
        "chr10",
        "chr11",
        "chr12",
        "chr13",
        "chr14",
        "chr15",
        "chr16",
        "chr17",
        "chr18",
        "chr19",
        "chr2",
        "chr20",
        "chr21",
        "chr22",
        "chr3",
        "chr4",
        "chr5",
        "chr6",
        "chr7",
        "chr8",
        "chr9",
        "chrx",
        "chry",
        "resident_regionsets",
        "snp_grch38",
        "snp_hg19",
    ]


def test_index_regions(regulome_elasticsearch_client):
    from genomic_data_service.region_indexer_task import index_regions_from_file
    from genomic_data_service.region_indexer import encode_graph

    query = ["accession=ENCFF760LBY"]

    file_properties = encode_graph(query)[0]
    file_uuid = file_properties["uuid"]
    dataset_accession = file_properties["dataset"].split("/")[2]
    dataset_accession = "accession=" + dataset_accession
    dataset_query = [dataset_accession]
    dataset = encode_graph(dataset_query)[0]
    # indexed_file = file_in_es(uuid, regulome_elasticsearch_client.es)
    index_regions_from_file(
        regulome_elasticsearch_client.es,
        file_uuid,
        file_properties,
        dataset,
        snp=False,
    )

    regulome_elasticsearch_client.es.indices.refresh()

    result = regulome_elasticsearch_client.es.search(
        index="chr10", body={"query": {"match_all": {}}}
    )
    assert result["hits"]["total"] == 18014
    assert "coordinates" in result["hits"]["hits"][0]["_source"]
    assert "strand" in result["hits"]["hits"][0]["_source"]
    assert "value" in result["hits"]["hits"][0]["_source"]
    assert "uuid" in result["hits"]["hits"][0]["_source"]

    result = regulome_elasticsearch_client.es.search(
        index="resident_regionsets", body={"query": {"match_all": {}}}
    )

    assert result["hits"]["total"] == 1
    assert result["hits"]["hits"][0]["_source"]["file"]["uuid"] == file_uuid
    assert "chroms" in result["hits"]["hits"][0]["_source"]
    assert "dataset" in result["hits"]["hits"][0]["_source"]
    assert "dataset_type" in result["hits"]["hits"][0]["_source"]
    assert "uuid" in result["hits"]["hits"][0]["_source"]
    assert "file" in result["hits"]["hits"][0]["_source"]
    assert "uses" in result["hits"]["hits"][0]["_source"]


def test_index_snps(regulome_elasticsearch_client):

    import uuid
    from genomic_data_service.region_indexer_task import (
        index_regions_from_test_snp_file,
    )
    from genomic_data_service.region_indexer import TEST_SNP_FILE, FILE_HG19

    file_uuid = uuid.uuid4()
    index_regions_from_test_snp_file(
        regulome_elasticsearch_client.es, file_uuid, TEST_SNP_FILE, FILE_HG19
    )
    regulome_elasticsearch_client.es.indices.refresh()
    result = regulome_elasticsearch_client.es.search(
        index="snp_hg19", body={"query": {"match_all": {}}}
    )

    assert result["hits"]["total"] == 11
    assert result["hits"]["hits"][0]["_type"] == "chr10"
    assert "alt_allele_freq" in result["hits"]["hits"][0]["_source"]
    assert "ref_allele_freq" in result["hits"]["hits"][0]["_source"]
    assert "coordinates" in result["hits"]["hits"][0]["_source"]
    assert "rsid" in result["hits"]["hits"][0]["_source"]
    assert "chrom" in result["hits"]["hits"][0]["_source"]
    assert "maf" in result["hits"]["hits"][0]["_source"]


def test_find_snp(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.find_snp("hg19", "rs10823321")
    assert res["maf"] == 0.1743
    assert res["chrom"] == "chr10"
    assert res["rsid"] == "rs10823321"
    assert res["chrom"] == "chr10"


def test_find_snps(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.find_snps("hg19", "chr10", 70989234, 70989284)
    assert len(res) == 11


def test_find_snps_exception(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.find_snps("hg9", "chrx", 70989234, 70989284)
    assert res == []


def test_find_peaks_filtered(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.find_peaks_filtered("hg19", "chr10", 70989234, 70989284)
    assert res[0][0]["_index"] == "chr10"
    assert res[0][0]["_type"] == "hg19"
    assert res[0][0]["_source"]["coordinates"] == {"gte": 70989195, "lt": 70989345}
    assert (
        res[0][0]["resident_detail"]["uuid"] == "dd2457d8-8216-41da-a025-cca739fd1312"
    )
    assert "dd2457d8-8216-41da-a025-cca739fd1312" in res[1]


def test_find_peaks_filtered_no_peak(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.find_peaks_filtered("hg19", "chrx", 70989234, 70989284)
    assert res == ([], None)


def test_nearby_snps(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.nearby_snps("hg19", "chr10", 70989270, "rs10823321")
    assert len(res) == 11


def test_str_score(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.str_score(1000)
    assert res == "1a"


def test_str_score_no_index(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.str_score(960)
    assert res == ""


def test_numeric_score(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.numeric_score("1a")
    assert res == 1000


def test_numeric_score_no_index(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.numeric_score("1z")
    assert res == 0


def test__scored_snps(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    snps = atlas._scored_snps("hg19", "chr10", 70989234, 70989284)
    snps = list(snps)

    assert len(snps) == 11
    assert snps[0]["chrom"] == "chr10"
    assert snps[0]["assembly"] == "hg19"
    assert "rsid" in snps[0]
    assert "score" in snps[0]
    assert "evidence" in snps[0]
    assert "coordinates" in snps[0]
    assert "ref_allele_freq" in snps[0]
    assert "alt_allele_freq" in snps[0]


def test__scored_snps_window(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    snps = atlas._scored_snps(
        "hg19", "chr10", 70989234, 70989284, window=5, center_pos=70989260
    )
    snps = list(snps)
    assert len(snps) == 5
    assert snps[0]["chrom"] == "chr10"
    assert snps[0]["assembly"] == "hg19"
    assert "rsid" in snps[0]
    assert "score" in snps[0]
    assert "evidence" in snps[0]
    assert "coordinates" in snps[0]
    assert "ref_allele_freq" in snps[0]
    assert "alt_allele_freq" in snps[0]


def test__scored_regions(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    regions = atlas._scored_regions("hg19", "chr10", 70989234, 70989284)
    regions = list(regions)
    region_start, region_end, region_score = regions[0]
    assert len(regions) == 1
    assert region_start == 70989234
    assert region_end == 70989283


def test__regulome_category_chip(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    dataset = {}
    dataset["collection_type"] = "chip-seq"
    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas._regulome_category(dataset=dataset)
    assert res == "Protein_Binding"


def test__regulome_category_dnase(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    dataset = {}
    dataset["collection_type"] = "dnase-seq"
    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas._regulome_category(dataset=dataset)
    assert res == "Chromatin_Structure"


def test__regulome_category_pwm(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    dataset = {}
    dataset["collection_type"] = "pwms"
    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas._regulome_category(dataset=dataset)
    assert res == "Motifs"


def test__regulome_category_footprints(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    dataset = {}
    dataset["collection_type"] = "footprints"
    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas._regulome_category(dataset=dataset)
    assert res == "Motifs"


def test__regulome_category_qtl(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    dataset = {}
    dataset["collection_type"] = "eqtls"
    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas._regulome_category(dataset=dataset)
    assert res == "Single_Nucleotides"


def test__regulome_category_none(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas._regulome_category()
    assert res == "???"


def test__regulome_category_invalid_category(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    dataset = {}
    dataset["collection_type"] = "other type"
    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas._regulome_category(dataset=dataset)
    assert res == "???"


def test_make_a_case(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    snp = {
        "rsid": "rs1187109723",
        "chrom": "chr10",
        "coordinates": {"gte": 70989245, "lt": 70989246},
        "ref_allele_freq": {"G": {"TOPMED": 1.0}},
        "alt_allele_freq": {"A": {"TOPMED": 7.964e-06}},
        "maf": 7.964e-06,
        "score": {"probability": "0.13454", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
        },
    }
    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    case = atlas.make_a_case(snp)
    assert case == {"DNase": "Chromatin_Structure:DNase:|ENCSR000EIT|GM03348|"}


def test_evidence_categories():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    res = RegulomeAtlas.evidence_categories()
    assert res == [
        "QTL",
        "ChIP",
        "DNase",
        "PWM",
        "Footprint",
        "PWM_matched",
        "Footprint_matched",
    ]


def test_iter_scored_snps(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    snps = atlas.iter_scored_snps("hg19", "chr10", 70989234, 70989284)
    snps = list(snps)
    assert len(snps) == 11
    assert snps[0]["chrom"] == "chr10"
    assert snps[0]["assembly"] == "hg19"
    assert "rsid" in snps[0]
    assert "score" in snps[0]
    assert "evidence" in snps[0]
    assert "coordinates" in snps[0]
    assert "ref_allele_freq" in snps[0]
    assert "alt_allele_freq" in snps[0]
    assert "maf" in snps[0]


def test_iter_scored_signal(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    res = atlas.iter_scored_signal("hg19", "chr10", 70989234, 70989284)
    res = list(res)
    start, end, score = res[0]
    assert len(res) == 1
    assert start == 70989234
    assert end == 70989283


def test_score_1a():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "QTL": {},
        "ChIP": {},
        "DNase": {},
        "PWM_matched": {},
        "Footprint_matched": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "1a"


def test_score_1b():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "QTL": {},
        "DNase": {},
        "ChIP": {},
        "PWM": {},
        "Footprint": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "1b"


def test_score_1c():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "QTL": {},
        "DNase": {},
        "ChIP": {},
        "PWM_matched": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "1c"


def test_score_1d():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "QTL": {},
        "DNase": {},
        "ChIP": {},
        "PWM": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "1d"


def test_score_1f():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "QTL": {},
        "ChIP": {},
        "DNase": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "1f"


def test_score_1f_2():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "QTL": {},
        "ChIP": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "1f"


def test_score_6():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "QTL": {},
        "PWM": {},
        "Footprint": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "6"


def test_score_2a():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "ChIP": {},
        "DNase": {},
        "PWM_matched": {},
        "Footprint_matched": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "2a"


def test_score_2b():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "ChIP": {},
        "DNase": {},
        "PWM": {},
        "Footprint": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "2b"


def test_score_2c():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "ChIP": {},
        "DNase": {},
        "PWM_matched": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "2c"


def test_score_3a():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "ChIP": {},
        "DNase": {},
        "PWM": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "3a"


def test_score_3b():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "ChIP": {},
        "PWM_matched": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "3b"


def test_score_4():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "ChIP": {},
        "DNase": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "4"


def test_score_6_2():
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    characterization = {
        "PWM": {},
        "Footprint": {},
        "IC_matched_max": 0.0,
        "IC_max": 0.0,
    }

    res = RegulomeAtlas._score(characterization)
    assert res["ranking"] == "6"


def test_regulome_score_none_evidence(regulome_elasticsearch_client):
    from genomic_data_service.regulome_atlas import RegulomeAtlas

    atlas = RegulomeAtlas(regulome_elasticsearch_client.es)
    datasets = {}
    evidence = None
    res = atlas.regulome_score(datasets, evidence)
    assert res == None


snps = [
    {
        "rsid": "rs1187109723",
        "chrom": "chr10",
        "coordinates": {"gte": 70989245, "lt": 70989246},
        "ref_allele_freq": {"G": {"TOPMED": 1.0}},
        "alt_allele_freq": {"A": {"TOPMED": 7.964e-06}},
        "maf": 7.964e-06,
        "score": {"probability": "0.13454", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 0.0,
        },
    },
    {
        "rsid": "rs539492586",
        "chrom": "chr10",
        "coordinates": {"gte": 70989254, "lt": 70989255},
        "ref_allele_freq": {"G": {"1000Genomes": 0.9992, "GnomAD": 1.0, "TOPMED": 1.0}},
        "alt_allele_freq": {
            "A": {"1000Genomes": 0.0007987, "GnomAD": 3.187e-05, "TOPMED": 3.982e-05}
        },
        "maf": 0.0007987,
        "score": {"probability": "0.12376", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 0.05999999865889549,
        },
    },
    {
        "rsid": "rs1203619109",
        "chrom": "chr10",
        "coordinates": {"gte": 70989262, "lt": 70989263},
        "ref_allele_freq": {"C": {"TOPMED": 1.0}},
        "alt_allele_freq": {"T": {"TOPMED": 7.964e-06}},
        "maf": 7.964e-06,
        "score": {"probability": "0.32483", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.23999999463558197,
            "IC_max": 1.9299999475479126,
        },
    },
    {
        "rsid": "rs115400561",
        "chrom": "chr10",
        "coordinates": {"gte": 70989273, "lt": 70989274},
        "ref_allele_freq": {
            "T": {
                "1000Genomes": 0.9888,
                "ALSPAC": 0.9995,
                "GnomAD": 0.9926,
                "TOPMED": 0.9916,
                "TWINSUK": 1.0,
            }
        },
        "alt_allele_freq": {
            "C": {
                "1000Genomes": 0.01118,
                "ALSPAC": 0.0005189,
                "GnomAD": 0.007363,
                "TOPMED": 0.008362,
                "TWINSUK": 0.0,
            }
        },
        "maf": 0.01118,
        "score": {"probability": "0.53672", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 1.6399999856948853,
            "IC_max": 1.8600000143051147,
        },
    },
    {
        "rsid": "rs1014437528",
        "chrom": "chr10",
        "coordinates": {"gte": 70989283, "lt": 70989284},
        "ref_allele_freq": {"A": {"TOPMED": 1.0}},
        "alt_allele_freq": {"G": {"TOPMED": 7.964e-06}, "T": {"TOPMED": 1.593e-05}},
        "maf": 1.593e-05,
        "score": {"probability": "0.13454", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 0.0,
        },
    },
    {
        "rsid": "rs185797602",
        "chrom": "chr10",
        "coordinates": {"gte": 70989234, "lt": 70989235},
        "ref_allele_freq": {
            "C": {
                "1000Genomes": 0.9998,
                "ALSPAC": 0.9997,
                "GnomAD": 1.0,
                "TOPMED": 0.9999,
                "TWINSUK": 1.0,
            }
        },
        "alt_allele_freq": {
            "T": {
                "1000Genomes": 0.0001997,
                "ALSPAC": 0.0002595,
                "GnomAD": 3.185e-05,
                "TOPMED": 0.0001195,
                "TWINSUK": 0.0,
            }
        },
        "maf": 0.0002595,
        "score": {"probability": "0.14657", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.7799999713897705,
        },
    },
    {
        "rsid": "rs1258348810",
        "chrom": "chr10",
        "coordinates": {"gte": 70989255, "lt": 70989256},
        "ref_allele_freq": {"GA": {"TOPMED": 1.0}},
        "alt_allele_freq": {"G": {"TOPMED": 7.964e-06}},
        "maf": 7.964e-06,
        "score": {"probability": "0.17224", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.340000033378601,
        },
    },
    {
        "rsid": "rs1436649807",
        "chrom": "chr10",
        "coordinates": {"gte": 70989264, "lt": 70989265},
        "ref_allele_freq": {"G": {"GnomAD": 1.0}},
        "alt_allele_freq": {"C": {"GnomAD": 3.185e-05}},
        "maf": 3.185e-05,
        "score": {"probability": "0.33344", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 1.7200000286102295,
            "IC_max": 1.7200000286102295,
        },
    },
    {
        "rsid": "rs10823321",
        "chrom": "chr10",
        "coordinates": {"gte": 70989269, "lt": 70989270},
        "ref_allele_freq": {
            "G": {
                "1000Genomes": 0.8257,
                "ALSPAC": 0.8884,
                "Estonian": 0.8951,
                "GnomAD": 0.8345,
                "NorthernSweden": 0.8767,
                "TOPMED": 0.8283,
                "TWINSUK": 0.9024,
                "Vietnamese": 0.8785,
            }
        },
        "alt_allele_freq": {
            "A": {
                "1000Genomes": 0.1743,
                "ALSPAC": 0.1116,
                "Estonian": 0.1049,
                "GnomAD": 0.1655,
                "NorthernSweden": 0.1233,
                "TOPMED": 0.1717,
                "TWINSUK": 0.09763,
                "Vietnamese": 0.1215,
            }
        },
        "maf": 0.1743,
        "score": {"probability": "0.31478", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 1.7799999713897705,
            "IC_max": 1.7799999713897705,
        },
    },
    {
        "rsid": "rs1056321941",
        "chrom": "chr10",
        "coordinates": {"gte": 70989279, "lt": 70989280},
        "ref_allele_freq": {"G": {"GnomAD": 1.0}},
        "alt_allele_freq": {"A": {"GnomAD": 3.186e-05}},
        "maf": 3.186e-05,
        "score": {"probability": "0.07619", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.840000033378601,
        },
    },
    {
        "rsid": "rs894637399",
        "chrom": "chr10",
        "coordinates": {"gte": 70989281, "lt": 70989282},
        "ref_allele_freq": {"G": {"TOPMED": 0.9999}},
        "alt_allele_freq": {"A": {"TOPMED": 2.389e-05}, "T": {"TOPMED": 3.186e-05}},
        "maf": 3.186e-05,
        "score": {"probability": "0.09704", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.090000033378601,
        },
    },
]

iters = [
    {
        "rsid": "rs1187109723",
        "chrom": "chr10",
        "coordinates": {"gte": 70989245, "lt": 70989246},
        "ref_allele_freq": {"G": {"TOPMED": 1.0}},
        "alt_allele_freq": {"A": {"TOPMED": 7.964e-06}},
        "maf": 7.964e-06,
        "score": {"probability": "0.13454", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 0.0,
        },
    },
    {
        "rsid": "rs539492586",
        "chrom": "chr10",
        "coordinates": {"gte": 70989254, "lt": 70989255},
        "ref_allele_freq": {"G": {"1000Genomes": 0.9992, "GnomAD": 1.0, "TOPMED": 1.0}},
        "alt_allele_freq": {
            "A": {"1000Genomes": 0.0007987, "GnomAD": 3.187e-05, "TOPMED": 3.982e-05}
        },
        "maf": 0.0007987,
        "score": {"probability": "0.12376", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 0.05999999865889549,
        },
    },
    {
        "rsid": "rs1203619109",
        "chrom": "chr10",
        "coordinates": {"gte": 70989262, "lt": 70989263},
        "ref_allele_freq": {"C": {"TOPMED": 1.0}},
        "alt_allele_freq": {"T": {"TOPMED": 7.964e-06}},
        "maf": 7.964e-06,
        "score": {"probability": "0.32483", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.23999999463558197,
            "IC_max": 1.9299999475479126,
        },
    },
    {
        "rsid": "rs115400561",
        "chrom": "chr10",
        "coordinates": {"gte": 70989273, "lt": 70989274},
        "ref_allele_freq": {
            "T": {
                "1000Genomes": 0.9888,
                "ALSPAC": 0.9995,
                "GnomAD": 0.9926,
                "TOPMED": 0.9916,
                "TWINSUK": 1.0,
            }
        },
        "alt_allele_freq": {
            "C": {
                "1000Genomes": 0.01118,
                "ALSPAC": 0.0005189,
                "GnomAD": 0.007363,
                "TOPMED": 0.008362,
                "TWINSUK": 0.0,
            }
        },
        "maf": 0.01118,
        "score": {"probability": "0.53672", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 1.6399999856948853,
            "IC_max": 1.8600000143051147,
        },
    },
    {
        "rsid": "rs1014437528",
        "chrom": "chr10",
        "coordinates": {"gte": 70989283, "lt": 70989284},
        "ref_allele_freq": {"A": {"TOPMED": 1.0}},
        "alt_allele_freq": {"G": {"TOPMED": 7.964e-06}, "T": {"TOPMED": 1.593e-05}},
        "maf": 1.593e-05,
        "score": {"probability": "0.13454", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 0.0,
        },
    },
    {
        "rsid": "rs185797602",
        "chrom": "chr10",
        "coordinates": {"gte": 70989234, "lt": 70989235},
        "ref_allele_freq": {
            "C": {
                "1000Genomes": 0.9998,
                "ALSPAC": 0.9997,
                "GnomAD": 1.0,
                "TOPMED": 0.9999,
                "TWINSUK": 1.0,
            }
        },
        "alt_allele_freq": {
            "T": {
                "1000Genomes": 0.0001997,
                "ALSPAC": 0.0002595,
                "GnomAD": 3.185e-05,
                "TOPMED": 0.0001195,
                "TWINSUK": 0.0,
            }
        },
        "maf": 0.0002595,
        "score": {"probability": "0.14657", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.7799999713897705,
        },
    },
    {
        "rsid": "rs1258348810",
        "chrom": "chr10",
        "coordinates": {"gte": 70989255, "lt": 70989256},
        "ref_allele_freq": {"GA": {"TOPMED": 1.0}},
        "alt_allele_freq": {"G": {"TOPMED": 7.964e-06}},
        "maf": 7.964e-06,
        "score": {"probability": "0.17224", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.340000033378601,
        },
    },
    {
        "rsid": "rs1436649807",
        "chrom": "chr10",
        "coordinates": {"gte": 70989264, "lt": 70989265},
        "ref_allele_freq": {"G": {"GnomAD": 1.0}},
        "alt_allele_freq": {"C": {"GnomAD": 3.185e-05}},
        "maf": 3.185e-05,
        "score": {"probability": "0.33344", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 1.7200000286102295,
            "IC_max": 1.7200000286102295,
        },
    },
    {
        "rsid": "rs10823321",
        "chrom": "chr10",
        "coordinates": {"gte": 70989269, "lt": 70989270},
        "ref_allele_freq": {
            "G": {
                "1000Genomes": 0.8257,
                "ALSPAC": 0.8884,
                "Estonian": 0.8951,
                "GnomAD": 0.8345,
                "NorthernSweden": 0.8767,
                "TOPMED": 0.8283,
                "TWINSUK": 0.9024,
                "Vietnamese": 0.8785,
            }
        },
        "alt_allele_freq": {
            "A": {
                "1000Genomes": 0.1743,
                "ALSPAC": 0.1116,
                "Estonian": 0.1049,
                "GnomAD": 0.1655,
                "NorthernSweden": 0.1233,
                "TOPMED": 0.1717,
                "TWINSUK": 0.09763,
                "Vietnamese": 0.1215,
            }
        },
        "maf": 0.1743,
        "score": {"probability": "0.31478", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 1.7799999713897705,
            "IC_max": 1.7799999713897705,
        },
    },
    {
        "rsid": "rs1056321941",
        "chrom": "chr10",
        "coordinates": {"gte": 70989279, "lt": 70989280},
        "ref_allele_freq": {"G": {"GnomAD": 1.0}},
        "alt_allele_freq": {"A": {"GnomAD": 3.186e-05}},
        "maf": 3.186e-05,
        "score": {"probability": "0.07619", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.840000033378601,
        },
    },
    {
        "rsid": "rs894637399",
        "chrom": "chr10",
        "coordinates": {"gte": 70989281, "lt": 70989282},
        "ref_allele_freq": {"G": {"TOPMED": 0.9999}},
        "alt_allele_freq": {"A": {"TOPMED": 2.389e-05}, "T": {"TOPMED": 3.186e-05}},
        "maf": 3.186e-05,
        "score": {"probability": "0.09704", "ranking": "5"},
        "assembly": "hg19",
        "evidence": {
            "DNase": [
                {
                    "uuid": "473170a0-9eb8-4fe7-ac97-6d35f1837fca",
                    "@id": "/experiments/ENCSR000EIT/",
                    "target": [],
                    "biosample_ontology": {
                        "dbxrefs": ["Cellosaurus:CVCL_7382"],
                        "organ_slims": ["connective tissue", "skin of body"],
                        "system_slims": ["integumental system"],
                        "aliases": [],
                        "references": [],
                        "@type": ["BiosampleType", "Item"],
                        "synonyms": ["GM03348"],
                        "term_id": "CLO:0016536",
                        "classification": "cell line",
                        "uuid": "d7a0d846-9744-423b-a6a3-1d1c9b82361e",
                        "schema_version": "1",
                        "term_name": "GM03348",
                        "cell_slims": ["fibroblast"],
                        "developmental_slims": ["ectoderm"],
                        "name": "cell_line_CLO_0016536",
                        "@id": "/biosample-types/cell_line_CLO_0016536/",
                        "status": "released",
                    },
                    "biosample_term_name": "GM03348",
                    "documents": [],
                    "collection_type": "DNase-seq",
                }
            ],
            "IC_matched_max": 0.0,
            "IC_max": 1.090000033378601,
        },
    },
]
