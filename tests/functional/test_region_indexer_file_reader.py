import pytest
from genomic_data_service.region_indexer_file_reader import FileReader, BedFileReader, SnpFileReader


def test_file_reader(bed_file):
    file_size = bed_file.get('file_size', 0)
    file_path = bed_file['s3_uri']
    reader = FileReader(file_path, {}, file_size)
    assert reader.file_path == file_path
    assert reader.file_size == file_size
    assert reader.strand_values == {}
    reader.close()


def test_should_load_file_in_memory_small_file_size(bed_file):
    file_size = bed_file.get('file_size', 0)
    file_path = bed_file['s3_uri']
    reader = FileReader(file_path, {}, file_size)
    assert reader.should_load_file_in_memory() == True
    reader.close()


def test_should_load_file_in_memory_no_file_size(bed_file):
    bed_file.pop("file_size")
    file_size = bed_file.get('file_size', 0)
    file_path = bed_file['s3_uri']
    reader = FileReader(file_path, {}, file_size)
    assert reader.should_load_file_in_memory() == False
    reader.close()


def test_should_load_file_in_memory_big_file_size(bed_file):
    bed_file["file_size"] = 26224400
    file_size = bed_file.get('file_size', 0)
    file_path = bed_file['s3_uri']
    reader = FileReader(file_path, {}, file_size)
    assert reader.should_load_file_in_memory() == False
    reader.close()


def test_close(bed_file):
    file_size = bed_file.get('file_size', 0)
    file_path = bed_file['s3_uri']
    reader = FileReader(file_path, {}, file_size)
    assert reader.temp_file.closed == False
    reader.close()
    assert reader.temp_file.closed


def test_parse(bed_file):
    file_size = bed_file.get('file_size', 0)
    file_path = bed_file['s3_uri']
    reader = BedFileReader(file_path, {}, file_size)
    doc_dict = list(reader.parse())
    assert len(doc_dict) == 300000

def test_parse_local():
    reader = SnpFileReader("./tests/data/test_snp_file.bed.gz", source="local")
    docs = list(reader.parse())
    assert len(docs) == 4

def test_snp_local():
    reader = SnpFileReader("./tests/data/test_snp_file.bed.gz", source="local")
    docs = list(reader.parse())
    (chrom, doc) = docs[3]
    assert chrom == "chr10"
    assert doc == {
        "chrom": "chr10",
        "coordinates": {"gte": 60089, "lt": 60090},
        "rsid": "rs1399657112",
        "maf": 7.964e-06,
        "ref_allele_freq": {"G": {"TOPMED": 1.0}},
        "alt_allele_freq": {"T": {"TOPMED": 7.964e-06}},
    }

def test_region(bed_file, value_strand_col_chip_seq):
    file_size = bed_file.get('file_size', 0)
    file_path = bed_file['s3_uri']
    reader = BedFileReader(file_path, value_strand_col_chip_seq, file_size)
    docs = list(reader.parse())
    (chrom, doc) = docs[0]
    assert chrom == "chr12"
    assert doc == {
        "coordinates": {"gte": 121887854, "lt": 121888984},
        "strand": ".",
        "value": "724.104457912132",
    }
