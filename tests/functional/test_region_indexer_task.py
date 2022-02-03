import pytest
from genomic_data_service.region_indexer_task import metadata_doc, list_targets


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
