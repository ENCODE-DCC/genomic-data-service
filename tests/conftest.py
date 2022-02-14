import pytest

from genomic_data_service import app


@pytest.fixture(scope="module")
def test_client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


@pytest.fixture
def query():
    return ["accession=ENCFF904UCL"]


@pytest.fixture
def dataset_no_doc_index():
    return {
        "uuid": "19b2ffe1-a645-4da5-ac4e-631f1629dca0",
        "@id": "/references/ENCSR942EOJ/",
        "target": [],
        "biosample_ontology": {},
        "biosample_term_name": None,
        "reference_type": "index",
        "documents": [],
        "@type": ["Reference", "FileSet", "Dataset", "Item"],
    }


@pytest.fixture
def dataset_no_doc_pwms():
    return {
        "@id": "/annotations/ENCSR601QZC/",
        "@type": ["Annotation", "FileSet", "Dataset", "Item"],
        "accession": "ENCSR601QZC",
        "annotation_type": "PWMs",
        "uuid": "19b2ffe1-a645-4da5-ac4e-631f1629dca0",
        "target": [],
        "biosample_ontology": {},
        "biosample_term_name": None,
        "documents": [],
    }


@pytest.fixture
def dataset_no_doc_chip_seq():
    return {
        "@id": "/experiments/ENCSR668LDD/",
        "@type": ["Experiment", "Dataset", "Item"],
        "accession": "ENCSR668LDD",
        "assay_term_name": "ChIP-seq",
        "assay_title": "Histone ChIP-seq",
        "assembly": ["GRCh38", "hg19"],
        "uuid": "934eed39-3a71-403c-85d0-d7b055f1269b",
        "target": [],
        "biosample_ontology": {},
        "biosample_term_name": None,
        "documents": [],
    }


@pytest.fixture
def document_string():
    return "/documents/49f43842-5ab4-4aa1-a6f4-2b1234955d93/"


@pytest.fixture
def document_dict():
    return [
        {
            "aliases": ["j-michael-cherry:regulome-PWMs_Elf3_pwm_primary.pwm"],
            "references": [],
            "date_created": "2021-02-28T07:25:47.062123+00:00",
            "@type": ["Document", "Item"],
            "submitted_by": "/users/76091563-a959-4a9c-929c-9acfa1a0a078/",
            "description": "Elf3_pwm_primary.pwm",
            "lab": "/labs/alan-boyle/",
            "uuid": "cae62161-3aff-4c7d-8bc2-e3b99f1e506e",
            "schema_version": "8",
            "urls": [],
            "award": "/awards/U41HG009293/",
            "attachment": {
                "download": "Elf3_pwm_primary.txt",
                "md5sum": "25a91e3bed218ae7b08157782dfa9a33",
                "href": "@@download/attachment/Elf3_pwm_primary.txt",
                "type": "text/plain",
            },
            "@id": "/documents/cae62161-3aff-4c7d-8bc2-e3b99f1e506e/",
            "status": "released",
            "document_type": "position weight matrix",
        }
    ]


@pytest.fixture
def files_filtered():
    return [
        {
            "@id": "/files/ENCFF084PQN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF084PQN",
            "assay_term_name": "ChIP-seq",
            "assembly": "hg19",
            "dataset": "/experiments/ENCSR668LDD/",
            "file_format": "bed",
            "file_type": "bed narrowPeak",
            "output_type": "peaks",
            "status": "released",
        },
        {
            "@id": "/files/ENCFF184PQN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF184PQN",
            "assay_term_name": "ChIP-seq",
            "assembly": "hg19",
            "dataset": "/experiments/ENCSR668LDD/",
            "file_format": "bed",
            "file_type": "bed narrowPeak",
            "output_type": "peaks",
            "status": "released",
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "archived",
        },
    ]


@pytest.fixture
def files_unfiltered():
    return [
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF849NZN",
            "assembly": "hg17",
            "file_format": "bed",
            "status": "archived",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "assay_term_name": "ChIP-seq",
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "txt",
            "status": "archived",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "assay_term_name": "ChIP-seq",
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "in progress",
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "non-ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "archived",
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "archived",
        },
        {
            "@id": "/files/ENCFF084PQN/",
            "@type": ["File", "Item"],
            "accession": "ENCFF084PQN",
            "assay_term_name": "ChIP-seq",
            "assembly": "hg19",
            "dataset": "/experiments/ENCSR668LDD/",
            "file_format": "bed",
            "file_type": "bed narrowPeak",
            "output_type": "peaks",
            "status": "released",
        },
    ]


@pytest.fixture
def bed_file():
    return {
        "@id": "/files/ENCFF849NZN/",
        "@type": ["File", "Item"],
        "accession": "ENCFF849NZN",
        "assembly": "GRCh38",
        "file_format": "bed",
        "assay_term_name": "ChIP-seq",
        "output_type": "peaks and background as input for IDR",
        "file_type": "bed narrowPeak",
        "dataset": "/experiments/ENCSR448UKK/",
        "s3_uri": "s3://encode-public/2016/10/28/f10f23fb-44fe-4496-bcab-8893ac3379a1/ENCFF849NZN.bed.gz",
        "file_size": 7165845,
        "uuid": "f10f23fb-44fe-4496-bcab-8893ac3379a1",
        "status": "archived",
    }


@pytest.fixture
def dataset_target():
    return {
        "schema_version": "14",
        "aliases": [],
        "organism": {
            "schema_version": "6",
            "@type": ["Organism", "Item"],
            "name": "human",
            "taxon_id": "9606",
            "scientific_name": "Homo sapiens",
            "@id": "/organisms/human/",
            "uuid": "7745b647-ff15-4ff3-9ced-b897d4e2983c",
            "status": "released",
        },
        "genes": [
            {
                "dbxrefs": [
                    "UniProtKB:Q59HG5",
                    "RefSeq:NM_001278122.2",
                    "UniProtKB:A0A024RCK7",
                    "UniProtKB:Q15776",
                    "GeneCards:ZKSCAN8",
                    "Vega:OTTHUMG00000014510",
                    "HGNC:12983",
                    "ENSEMBL:ENSG00000198315",
                    "MIM:602240",
                ],
                "symbol": "ZKSCAN8",
                "organism": "/organisms/human/",
                "synonyms": ["LD5-1", "ZNF192", "ZSCAN40"],
                "@type": ["Gene", "Item"],
                "title": "ZKSCAN8 (Homo sapiens)",
                "uuid": "0db99c4e-2c4f-40af-85ea-a162a417e666",
                "targets": [
                    "/targets/eGFP-ZKSCAN8-human/",
                    "/targets/ZKSCAN8-human/",
                    "/targets/3xFLAG-ZKSCAN8-human/",
                ],
                "schema_version": "3",
                "geneid": "7745",
                "name": "zinc finger with KRAB and SCAN domains 8",
                "locations": [
                    {
                        "chromosome": "chr6",
                        "assembly": "GRCh38",
                        "start": 28141883,
                        "end": 28159460,
                    },
                    {
                        "chromosome": "chr6",
                        "assembly": "hg19",
                        "start": 28109661,
                        "end": 28127238,
                    },
                ],
                "@id": "/genes/7745/",
                "ncbi_entrez_status": "live",
                "status": "released",
            }
        ],
        "@type": ["Target", "Item"],
        "name": "ZKSCAN8-human",
        "label": "ZKSCAN8",
        "@id": "/targets/ZKSCAN8-human/",
        "title": "ZKSCAN8 (Homo sapiens)",
        "investigated_as": ["transcription factor"],
        "uuid": "aff0558c-2b9c-4594-bf23-082d9e9af5d2",
        "status": "released",
    }


@pytest.fixture
def dataset_targets():
    return [
        {
            "schema_version": "14",
            "aliases": ["michael-snyder:TS-1311"],
            "organism": "/organisms/human/",
            "genes": [
                {
                    "dbxrefs": [
                        "ENSEMBL:ENSG00000135373",
                        "MIM:605439",
                        "RefSeq:NM_012153.6",
                        "HGNC:3246",
                        "Vega:OTTHUMG00000166454",
                        "GeneCards:EHF",
                        "UniProtKB:Q9NZC4",
                    ],
                    "symbol": "EHF",
                    "organism": "/organisms/human/",
                    "synonyms": ["ESE3", "ESE3B", "ESEJ"],
                    "@type": ["Gene", "Item"],
                    "title": "EHF (Homo sapiens)",
                    "uuid": "64687ad0-44fa-4940-8cd0-60987932499d",
                    "targets": ["/targets/eGFP-EHF-human/", "/targets/EHF-human/"],
                    "schema_version": "3",
                    "geneid": "26298",
                    "name": "ETS homologous factor",
                    "locations": [
                        {
                            "chromosome": "chr11",
                            "assembly": "GRCh38",
                            "start": 34621093,
                            "end": 34663288,
                        },
                        {
                            "chromosome": "chr11",
                            "assembly": "hg19",
                            "start": 34642640,
                            "end": 34684835,
                        },
                    ],
                    "@id": "/genes/26298/",
                    "ncbi_entrez_status": "live",
                    "status": "released",
                }
            ],
            "@type": ["Target", "Item"],
            "name": "EHF-human",
            "label": "EHF",
            "@id": "/targets/EHF-human/",
            "title": "EHF (Homo sapiens)",
            "investigated_as": ["transcription factor"],
            "uuid": "76612f65-137a-44fa-931a-5934b5212f4e",
            "status": "released",
        }
    ]


@pytest.fixture
def value_strand_col_chip_seq():
    return {"strand_col": 5, "value_col": 6}


from contextlib import contextmanager


@contextmanager
def start_elasticsearch(host="localhost", port=9203):
    import io
    import os
    import shutil
    import subprocess
    import tempfile

    data_directory = tempfile.mkdtemp()
    command = [
        "elasticsearch",
        f"-Enetwork.host={host}",
        f"-Ehttp.port={port}",
        f'-Epath.data={os.path.join(data_directory, "data")}',
        f'-Epath.logs={os.path.join(data_directory, "logs")}',
        f"-Epath.conf=./genomic_data_service/rnaseq/tests/elasticsearch/conf",
    ]
    process = subprocess.Popen(
        command,
        close_fds=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
        print(line)
        if "started" in line:
            print("ES up and running")
            break
    try:
        print("yielding ES")
        yield process
    finally:
        print("cleaning up ES")
        process.terminate()
        process.wait()
        shutil.rmtree(data_directory)


@pytest.fixture(scope="session")
def regulome_elasticsearch_client(host="127.0.0.1", port=9203):
    from genomic_data_service.region_indexer_elastic_search import (
        RegionIndexerElasticSearch,
    )
    from genomic_data_service.region_indexer import (
        SUPPORTED_CHROMOSOMES,
        SUPPORTED_ASSEMBLIES,
    )

    with start_elasticsearch(host=host, port=port) as process:
        yield RegionIndexerElasticSearch(
            host, port, SUPPORTED_CHROMOSOMES, SUPPORTED_ASSEMBLIES
        )
