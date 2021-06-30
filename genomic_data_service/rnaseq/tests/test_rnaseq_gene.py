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
        'ENSG00000224939',
    ]
    gene.props['dbxrefs'].append('ENSEMBL:ENSG00000221650')
    gene._extract_ensembl_ids()
    assert gene._ensembl_ids == [
        'ENSG00000224939',
        'ENSG00000221650',
    ]


def test_rnaseq_gene_extract_gene_properties(raw_human_genes):
    from genomic_data_service.rnaseq.domain.gene import Gene
    gene = Gene(raw_human_genes[0])
    gene._extract_gene_properties()
    assert gene._gene_properties == {
        'geneid': '100302691',
        'name': 'long intergenic non-protein coding RNA 184',
        'symbol': 'LINC00184',
        'synonyms': ['HANC', 'NCRNA00184'],
        'title': 'LINC00184 (Homo sapiens)'
    }


def test_rnaseq_gene_by_ensembl_ids(raw_human_genes):
    from genomic_data_service.rnaseq.domain.gene import Gene
    gene = Gene(raw_human_genes[0])
    gene_by_ensembl_ids = list(gene.by_ensembl_ids())
    assert gene_by_ensembl_ids == [
        (
            'ENSG00000224939',
            {
                'geneid': '100302691',
                'name': 'long intergenic non-protein coding RNA 184',
                'symbol': 'LINC00184',
                'synonyms': ['HANC', 'NCRNA00184'],
                'title': 'LINC00184 (Homo sapiens)'
            }
        )
    ]
    gene.props['dbxrefs'].append('ENSEMBL:ENSG00000221650')
    gene_by_ensembl_ids = list(gene.by_ensembl_ids())
    assert gene_by_ensembl_ids == [
        (
            'ENSG00000224939',
            {
                'geneid': '100302691',
                'name': 'long intergenic non-protein coding RNA 184',
                'symbol': 'LINC00184',
                'synonyms': ['HANC', 'NCRNA00184'],
                'title': 'LINC00184 (Homo sapiens)'
            }
        ),
        (
            'ENSG00000221650',
            {
                'geneid': '100302691',
                'name': 'long intergenic non-protein coding RNA 184',
                'symbol': 'LINC00184',
                'synonyms': ['HANC', 'NCRNA00184'],
                'title': 'LINC00184 (Homo sapiens)'
            }
        )
    ]
