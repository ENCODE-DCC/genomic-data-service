import pytest


def test_rnaseq_remote_portal_init():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert isinstance(portal, Portal)


def test_rnaseq_remote_portal_get_gene_url():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert portal._get_gene_url() == (
        'https://www.encodeproject.org/search/'
        '?type=Gene&advancedQuery=dbxrefs:ENSEMBL*'
        '&organism.scientific_name=Homo+sapiens'
        '&organism.scientific_name=Mus+musculus'
        '&field=@id&field=dbxrefs&field=geneid'
        '&field=name&field=organism.scientific_name'
        '&field=symbol&field=synonyms&field=title'
        '&format=json&limit=all'
    )


def test_rnaseq_remote_portal_get_dataset_url():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert portal._get_dataset_url() == (
        'https://www.encodeproject.org/search/'
        '?type=Experiment&status=released&assay_title=polyA+plus+RNA-seq'
        '&assay_title=total+RNA-seq&assay_title=polyA+minus+RNA-seq'
        '&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens'
        '&replicates.library.biosample.donor.organism.scientific_name=Mus+musculus'
        '&assembly=GRCh38&assembly=mm10&files.file_type=tsv'
        '&field=biosample_summary'
        '&field=replicates.library.biosample.sex'
        '&field=replicates.library.biosample.age'
        '&field=replicates.library.biosample.age_units'
        '&field=replicates.library.biosample.donor.organism.scientific_name'
        '&format=json&limit=all'
    )


def test_rnaseq_remote_portal_get_file_url():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert portal._get_file_url() == (
        'https://www.encodeproject.org/search/'
        '?type=File&status=released&output_type=gene+quantifications'
        '&output_category=quantification&file_format=tsv&assembly=GRCh38&assembly=mm10'
        '&assay_title=polyA+plus+RNA-seq&assay_title=total+RNA-seq&assay_title=polyA+minus+RNA-seq'
        '&lab.title=ENCODE+Processing+Pipeline'
        '&genome_annotation=V29'
        '&genome_annotation=M21'
        '&preferred_default=true'
        '&field=assay_title&field=assembly'
        '&field=biosample_ontology.organ_slims&field=biosample_ontology.term_name'
        '&field=biosample_ontology.synonyms&field=biosample_ontology.name&field=biosample_ontology.term_id'
        '&field=biosample_ontology.classification&field=dataset'
        '&field=donors&field=file_type&field=genome_annotation&field=href'
        '&field=md5sum&field=output_type&field=s3_uri&field=title'
        '&format=json&limit=all'
    )


def test_rnaseq_remote_portal_load_genes(mocker, raw_human_genes):
    from genomic_data_service.rnaseq.remote.portal import Portal
    mocker.patch(
        'genomic_data_service.rnaseq.remote.portal.get_json',
        return_value={
            '@graph': raw_human_genes
        }
    )
    portal = Portal()
    portal.load_genes()
    assert 'genes' in portal.repositories
    assert len(portal.repositories['genes']) == 5
    expected_gene_ids = [
        'ENSG00000224939',
        'ENSG00000283857',
        'ENSG00000260442',
        'ENSG00000221650',
        'ENSG00000034677',
    ]
    for expected_gene_id in expected_gene_ids:
        assert expected_gene_id in portal.repositories['genes']


def test_rnaseq_remote_portal_load_datasets(mocker, raw_datasets):
    from genomic_data_service.rnaseq.remote.portal import Portal
    mocker.patch(
        'genomic_data_service.rnaseq.remote.portal.get_json',
        return_value={
            '@graph': raw_datasets
        }
    )
    portal = Portal()
    portal.load_datasets()
    assert 'datasets' in portal.repositories
    assert len(portal.repositories['datasets']) == 3
    expected_dataset_ids = [
        '/experiments/ENCSR113HQM/',
        '/experiments/ENCSR906HEV/',
        '/experiments/ENCSR938LSP/',
    ]
    for expected_dataset_id in expected_dataset_ids:
        assert expected_dataset_id in portal.repositories['datasets']


def test_rnaseq_remote_portal_get_rna_seq_files(mock_portal):
    files = list(mock_portal.get_rna_seq_files())
    assert len(files) == 4
