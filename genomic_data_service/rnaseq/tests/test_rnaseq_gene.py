import pytest


def test_rnaseq_gene_init():
    from genomic_data_service.rnaseq.domain.gene import Gene

    gene = Gene({})
    assert gene.props == {}
    assert isinstance(gene, Gene)


def test_rnaseq_gene_extract_ensembl_ids(raw_human_genes):
    from genomic_data_service.rnaseq.domain.gene import Gene

    gene = Gene(raw_human_genes[0])
    gene._extract_ensembl_ids()
    assert gene._ensembl_ids == [
        "ENSG00000224939",
    ]
    gene.props["dbxrefs"].append("ENSEMBL:ENSG00000221650")
    gene._extract_ensembl_ids()
    assert gene._ensembl_ids == [
        "ENSG00000224939",
        "ENSG00000221650",
    ]


def test_rnaseq_gene_extract_gene_properties(raw_human_genes):
    from genomic_data_service.rnaseq.domain.gene import Gene

    gene = Gene(raw_human_genes[0])
    gene._extract_gene_properties()
    assert gene._gene_properties == {
        "geneid": "100302691",
        "name": "long intergenic non-protein coding RNA 184",
        "symbol": "LINC00184",
        "synonyms": ["HANC", "NCRNA00184"],
        "title": "LINC00184 (Homo sapiens)",
        "@id": "/genes/100302691/",
    }


def test_rnaseq_gene_by_ensembl_ids(raw_human_genes):
    from genomic_data_service.rnaseq.domain.gene import Gene

    gene = Gene(raw_human_genes[0])
    gene_by_ensembl_ids = list(gene.by_ensembl_ids())
    assert gene_by_ensembl_ids == [
        (
            "ENSG00000224939",
            {
                "geneid": "100302691",
                "name": "long intergenic non-protein coding RNA 184",
                "symbol": "LINC00184",
                "synonyms": ["HANC", "NCRNA00184"],
                "title": "LINC00184 (Homo sapiens)",
                "@id": "/genes/100302691/",
            },
        )
    ]
    gene.props["dbxrefs"].append("ENSEMBL:ENSG00000221650")
    gene_by_ensembl_ids = list(gene.by_ensembl_ids())
    assert gene_by_ensembl_ids == [
        (
            "ENSG00000224939",
            {
                "geneid": "100302691",
                "name": "long intergenic non-protein coding RNA 184",
                "symbol": "LINC00184",
                "synonyms": ["HANC", "NCRNA00184"],
                "title": "LINC00184 (Homo sapiens)",
                "@id": "/genes/100302691/",
            },
        ),
        (
            "ENSG00000221650",
            {
                "geneid": "100302691",
                "name": "long intergenic non-protein coding RNA 184",
                "symbol": "LINC00184",
                "synonyms": ["HANC", "NCRNA00184"],
                "title": "LINC00184 (Homo sapiens)",
                "@id": "/genes/100302691/",
            },
        ),
    ]


def test_rnaseq_gene_get_genes_by_ensembl_id(human_genes):
    from genomic_data_service.rnaseq.domain.gene import get_genes_by_ensembl_id

    genes_by_ensembl_id = get_genes_by_ensembl_id(human_genes)
    assert genes_by_ensembl_id == {
        "ENSG00000224939": {
            "@id": "/genes/100302691/",
            "geneid": "100302691",
            "name": "long intergenic non-protein coding RNA 184",
            "symbol": "LINC00184",
            "synonyms": ["HANC", "NCRNA00184"],
            "title": "LINC00184 (Homo sapiens)",
        },
        "ENSG00000283857": {
            "@id": "/genes/100302145/",
            "geneid": "100302145",
            "name": "microRNA 1247",
            "symbol": "MIR1247",
            "synonyms": ["MIRN1247", "hsa-mir-1247", "mir-1247"],
            "title": "MIR1247 (Homo sapiens)",
        },
        "ENSG00000260442": {
            "@id": "/genes/100289092/",
            "geneid": "100289092",
            "name": "ATP2A1 antisense RNA 1",
            "symbol": "ATP2A1-AS1",
            "title": "ATP2A1-AS1 (Homo sapiens)",
        },
        "ENSG00000221650": {
            "@id": "/genes/100302286/",
            "geneid": "100302286",
            "name": "microRNA 1267",
            "symbol": "MIR1267",
            "synonyms": ["MIRN1267", "hsa-mir-1267"],
            "title": "MIR1267 (Homo sapiens)",
        },
        "ENSG00000034677": {
            "geneid": "25897",
            "symbol": "RNF19A",
            "name": "ring finger protein 19A, RBR E3 ubiquitin protein ligase",
            "synonyms": ["DKFZp566B1346", "RNF19", "dorfin"],
            "@id": "/genes/25897/",
            "title": "RNF19A (Homo sapiens)",
        },
    }
    assert len(genes_by_ensembl_id) == 5
    human_genes[0].props["dbxrefs"].append("ENSEMBL:ENSG00000221444")
    genes_by_ensembl_id = get_genes_by_ensembl_id(human_genes)
    assert len(genes_by_ensembl_id) == 6
    assert (
        genes_by_ensembl_id["ENSG00000224939"] == genes_by_ensembl_id["ENSG00000221444"]
    )
