import pytest
from genomic_data_service.region_indexer import encode_graph, clean_up, FILE_REQUIRED_FIELDS, need_to_fetch_documents, filter_files
from genomic_data_service.region_indexer import dataset_accession, fetch_datasets, print_progress_bar, log

def test_encode_graph(query):
    graph = encode_graph(query)[0]
    assert graph["@id"] == "/files/ENCFF904UCL/"
    assert graph["assembly"] == "GRCh38"
    assert graph["file_format"] == "bed"

def test_clean_up(query):
    graph = encode_graph(query)[0]
    clean_up_graph = clean_up(graph, FILE_REQUIRED_FIELDS)
    for key in clean_up_graph.keys():
        assert key in FILE_REQUIRED_FIELDS

def test_need_to_fetch_documents_no_doc(dataset_no_doc):
    assert need_to_fetch_documents(dataset_no_doc) == False

def test_need_to_fetch_documents_dict_doc(dataset_no_doc, document_dict):
    dataset = dataset_no_doc
    dataset['documet'] = document_dict
    assert need_to_fetch_documents(dataset_no_doc) == False

def test_filter_files(files_unfiltered):
    files = filter_files(files_unfiltered)
    assert len(files) == 2

def test_dataset_accession(bed_file):
    accession = dataset_accession(bed_file)
    assert accession == "ENCSR448UKK"
    file = bed_file.pop("dataset")
    accession = dataset_accession(file)
    assert accession == None

def test_fetch_datasets(files_filtered):
    datasets = {}
    fetch_datasets(files_filtered, datasets)
    assert len(datasets) == 2

def test_print_progress_bar(capsys):
    print_progress_bar(1, 10)
    captured = capsys.readouterr()
    assert captured.out == "\rProgress: |████████------------------------------------------------------------------------| 10.0% Complete\r"

def test_print_progress_bar_total(capsys):
    print_progress_bar(10, 10)
    captured = capsys.readouterr()
    assert captured.out == "\rProgress: |████████████████████████████████████████████████████████████████████████████████| 100.0% Complete\r\n"

def test_log(capsys):
    log("test", True)
    captured = capsys.readouterr()
    assert captured.out == "test\n"

