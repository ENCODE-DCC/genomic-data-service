import pytest
from genomic_data_service.region_indexer_file_reader import S3BedFileRemoteReader


def test_S3BedFileRemoteReader(bed_file):
    reader = S3BedFileRemoteReader(bed_file, {})
    assert reader.file_properties == bed_file
    assert reader.snp_set == False
    assert reader.strand_values == {}
    reader.close()


def test_should_load_file_in_memory_small_file_size(bed_file):
    reader = S3BedFileRemoteReader(bed_file, {})
    assert reader.should_load_file_in_memory() == True
    reader.close()


def test_should_load_file_in_memory_no_file_size(bed_file):
    bed_file.pop("file_size")
    reader = S3BedFileRemoteReader(bed_file, {})
    assert reader.should_load_file_in_memory() == False
    reader.close()


def test_should_load_file_in_memory_big_file_size(bed_file):
    bed_file["file_size"] = 26224400
    reader = S3BedFileRemoteReader(bed_file, {})
    assert reader.should_load_file_in_memory() == False
    reader.close()


def test_close(bed_file):
    reader = S3BedFileRemoteReader(bed_file, {})
    assert reader.temp_file.closed == False
    reader.close()
    assert reader.temp_file.closed


def test_parse(bed_file):
    reader = S3BedFileRemoteReader(bed_file, {})
    doc_dict = list(reader.parse())
    assert len(doc_dict) == 300000


def test_region(bed_file, value_strand_col_chip_seq):
    reader = S3BedFileRemoteReader(bed_file, value_strand_col_chip_seq)
    docs = list(reader.parse())
    (chrom, doc) = docs[0]
    assert chrom == "chr12"
    assert doc == {
        "coordinates": {"gte": 121887854, "lt": 121888984},
        "strand": ".",
        "value": "724.104457912132",
    }
