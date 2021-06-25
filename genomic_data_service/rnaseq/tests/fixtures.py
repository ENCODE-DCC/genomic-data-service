import pytest

@pytest.fixture
def expressions():
    return [
        {
            "annotation": "GRCh38",
            "assayType": "shRNA knockdown followed by RNA-seq",
            "biosample_classification": "cell line",
            "biosample_organ": "exocrine gland, epithelium, liver, endocrine gland",
            "biosample_sex": "male",
            "biosample_summary": "Homo sapiens HepG2 cell line expressing RNAi targeting GNB2L1",
            "biosample_system": "digestive system, endocrine system, exocrine system",
            "biosample_term_name": "HepG2",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF007FIZ",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR116YMU",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR116YMU",
            "tpm": "70.00"
        },
        {
            "annotation": "GRCh38",
            "assayType": "CRISPR genome editing followed by RNA-seq",
            "biosample_classification": "cell line",
            "biosample_organ": "blood, bodily fluid",
            "biosample_sex": "female",
            "biosample_summary": "Homo sapiens K562 cell line genetically modified (deletion) using CRISPR targeting FXR2",
            "biosample_system": "immune system",
            "biosample_term_name": "K562",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF006ECV",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR376GHG",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR376GHG",
            "tpm": "38.10"
        },
        {
            "annotation": "GRCh38",
            "assayType": "polyA plus RNA-seq",
            "biosample_classification": "tissue",
            "biosample_organ": "musculature of body, limb",
            "biosample_sex": "unknown",
            "biosample_summary": "Homo sapiens embryo (101 days) muscle of arm tissue",
            "biosample_system": "musculature",
            "biosample_term_name": "muscle of arm",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF007LRI",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR677MYO",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR677MYO",
            "tpm": "1.40"
        },
    ]
