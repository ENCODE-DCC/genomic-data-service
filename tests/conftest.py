import pytest

from genomic_data_service import app

@pytest.fixture(scope='module')
def test_client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

@pytest.fixture
def query():
    return ['accession=ENCFF904UCL']

@pytest.fixture
def dataset_no_doc():
    return {
        "uuid": "19b2ffe1-a645-4da5-ac4e-631f1629dca0",
        "@id": "/references/ENCSR942EOJ/",
        "target": [],
        "biosample_ontology": {},
        'biosample_term_name': None,
        "reference_type": "index",
        "documents": [],
        "@type": [
        "Reference",
        "FileSet",
        "Dataset",
        "Item"
        ],
    }

@pytest.fixture
def document_dict():
    return  [
        {
          "aliases": [
            "j-michael-cherry:regulome-PWMs_Elf3_pwm_primary.pwm"
          ],
          "references": [],
          "date_created": "2021-02-28T07:25:47.062123+00:00",
          "@type": [
            "Document",
            "Item"
          ],
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
            "type": "text/plain"
          },
          "@id": "/documents/cae62161-3aff-4c7d-8bc2-e3b99f1e506e/",
          "status": "released",
          "document_type": "position weight matrix"
        }
      ]

@pytest.fixture
def files_filtered():
    return [
        {
            "@id": "/files/ENCFF084PQN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF084PQN",
            "assay_term_name": "ChIP-seq",
            "assembly": "hg19",
            "dataset": "/experiments/ENCSR668LDD/",
            "file_format": "bed",
            "file_type": "bed narrowPeak",
            "output_type": "peaks",
            "status": "released"

        },
        {
            "@id": "/files/ENCFF184PQN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF184PQN",
            "assay_term_name": "ChIP-seq",
            "assembly": "hg19",
            "dataset": "/experiments/ENCSR668LDD/",
            "file_format": "bed",
            "file_type": "bed narrowPeak",
            "output_type": "peaks",
            "status": "released"

        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "archived"
        },
    ]

@pytest.fixture
def files_unfiltered():
    return [
        {

            "@id": "/files/ENCFF849NZN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF849NZN",
            "assembly": "hg17",
            "file_format": "bed",
            "status": "archived",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "assay_term_name": "ChIP-seq"
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "txt",
            "status": "archived",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "assay_term_name": "ChIP-seq"
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "in progress"
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "non-ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "archived"
        },
        {
            "@id": "/files/ENCFF849NZN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF849NZN",
            "assembly": "GRCh38",
            "file_format": "bed",
            "assay_term_name": "ChIP-seq",
            "output_type": "peaks and background as input for IDR",
            "file_type": "bed narrowPeak",
            "dataset": "/experiments/ENCSR448UKK/",
            "status": "archived"
        },
        {
            "@id": "/files/ENCFF084PQN/",
            "@type": [
                "File",
                "Item"
            ],
            "accession": "ENCFF084PQN",
            "assay_term_name": "ChIP-seq",
            "assembly": "hg19",
            "dataset": "/experiments/ENCSR668LDD/",
            "file_format": "bed",
            "file_type": "bed narrowPeak",
            "output_type": "peaks",
            "status": "released"

        }
    ]

@pytest.fixture
def bed_file():
    return {
        
        "@id": "/files/ENCFF849NZN/",
        "@type": [
            "File",
            "Item"
        ],
        "accession": "ENCFF849NZN",
        "assembly": "GRCh38",
        "file_format": "bed",
        "assay_term_name": "ChIP-seq",
        "output_type": "peaks and background as input for IDR",
        "file_type": "bed narrowPeak",
        "dataset": "/experiments/ENCSR448UKK/",
        "status": "archived"
        
    }