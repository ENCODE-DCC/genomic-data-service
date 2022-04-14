import pytest
from genomic_data_service.region_indexer_task import metadata_doc, list_targets, get_cols_for_index


def test_list_targets(dataset_no_doc_pwms, dataset_target):
    dataset = dataset_no_doc_pwms
    dataset["target"] = dataset_target
    target_labels = list_targets(dataset)
    assert target_labels == ["ZKSCAN8"]


def test_metadata_doc(bed_file, dataset_no_doc_pwms, document_string):
    uuid = bed_file["uuid"]
    dataset = dataset_no_doc_pwms
    dataset["documents"].append(document_string)
    meta_doc = metadata_doc(uuid, bed_file, dataset)
    assert meta_doc == {
        "dataset": {
            "@id": "/annotations/ENCSR601QZC/",
            "biosample_ontology": {},
            "biosample_term_name": None,
            "collection_type": "PWMs",
            "documents": ["/documents/49f43842-5ab4-4aa1-a6f4-2b1234955d93/"],
            "target": [],
            "uuid": "19b2ffe1-a645-4da5-ac4e-631f1629dca0",
            "description" : None
        },
        "dataset_type": "Annotation",
        "file": {
            "@id": "/files/ENCFF849NZN/",
            "assembly": "GRCh38",
            "uuid": "f10f23fb-44fe-4496-bcab-8893ac3379a1",
        },
        "uses": "regulomedb",
        "uuid": "f10f23fb-44fe-4496-bcab-8893ac3379a1",
    }

def test_get_cols_for_index_footprints():
    metadata = {
        "dataset": {
            "collection_type": "footprints"
        }
    }
    cols_for_index = get_cols_for_index(metadata)

    assert cols_for_index == {'strand_col': 5,}

def test_get_cols_for_index_eqtls():
    metadata = {
        "file": {
            "uuid": "0da420c0-23c8-4581-a93d-713a7ed4bae1",
            "@id": "/files/ENCFF356HNQ/",
            "assembly": "grch38",
        },
        "dataset": {
            "collection_type": "eqtls",
        }
    }
    cols_for_index = get_cols_for_index(metadata)

    assert cols_for_index == {
        'name_col': 3,
        'ensg_id_col': 8,
        'p_value_col': 14,
        'effect_size_col': 15
    }

