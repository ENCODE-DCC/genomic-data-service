import pytest
from genomic_data_service.gene_name_lookup import gene_name_lookup
from unittest.mock import patch


def test_gene_name_lookup():
    gene_name = gene_name_lookup("ENSG00000162367")
    assert gene_name == "TAL1"


def test_gene_name_lookup_none():
    gene_name = gene_name_lookup("ENSGI00000162367")
    assert gene_name == None
