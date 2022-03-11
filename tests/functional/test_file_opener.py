import pytest
from genomic_data_service.file_opener import LocalFileOpener, S3FileOpener


def test_LocalFileOpener():
    reader = LocalFileOpener("./tests/data/test_snp_file.bed.gz").open()
    num_of_lines = len(list(reader))
    assert num_of_lines == 4

def test_S3FileOpener_small_file(s3_uri):
    file_size = 200
    reader = S3FileOpener(s3_uri, file_size).open()
    num_of_lines = len(list(reader))
    assert num_of_lines == 7

def test_S3FileOpener_big_file(s3_uri):
    file_size = 0    
    reader = S3FileOpener(s3_uri, file_size).open()
    num_of_lines = len(list(reader))
    assert num_of_lines == 7

def test_close(s3_uri):
    file_size = 0    
    file_opener = S3FileOpener(s3_uri, file_size)
    file_opener.open()
    assert file_opener.temp_file.closed == False
    file_opener.close()
    assert file_opener.temp_file.closed
