AT_GRAPH = '@graph'

BASE_URL = 'https://www.encodeproject.org'

SEARCH_PATH = '/search/'

FILE_PARAMS = (
    '?type=File'
    '&status=released'
    '&output_type=gene+quantifications'
    '&output_category=quantification'
    '&file_format=tsv'
    '&assembly=GRCh38'
    '&assembly=mm10'
    '&assay_title=polyA+plus+RNA-seq'
    '&assay_title=total+RNA-seq'
    '&assay_title=small+RNA-seq'
    '&assay_title=polyA+minus+RNA-seq'
    '&field=assay_title'
    '&field=assembly'
    '&field=biosample_ontology.organ_slims'
    '&field=biosample_ontology.term_name'
    '&field=biosample_ontology.synonyms'
    '&field=biosample_ontology.name'
    '&field=biosample_ontology.term_id'
    '&field=biosample_ontology.classification'
    '&field=dataset'
    '&field=donors'
    '&field=file_type'
    '&field=genome_annotation'
    '&field=href'
    '&field=md5sum'
    '&field=output_type'
    '&field=s3_uri'
    '&field=title'
    '&format=json'
    '&limit=all'
)


DATASET_PARAMS = (
    '?type=Experiment'
    '&status=released'
    '&assay_title=polyA+plus+RNA-seq'
    '&assay_title=total+RNA-seq'
    '&assay_title=small+RNA-seq'
    '&assay_title=polyA+minus+RNA-seq'
    '&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens'
    '&replicates.library.biosample.donor.organism.scientific_name=Mus+musculus'
    '&assembly=GRCh38'
    '&assembly=mm10'
    '&files.file_type=tsv'
    '&field=biosample_summary'
    '&field=replicates.library.biosample.sex'
    '&field=replicates.library.biosample.age'
    '&field=replicates.library.biosample.age_units'
    '&format=json'
    '&limit=all'
)


GENE_PARAMS = (
    '?type=Gene'
    '&advancedQuery=dbxrefs:ENSEMBL*'
    '&organism.scientific_name=Homo+sapiens'
    '&organism.scientific_name=Mus+musculus'
    '&field=@id'
    '&field=dbxrefs'
    '&field=geneid'
    '&field=name'
    '&field=organism.scientific_name'
    '&field=symbol'
    '&field=synonyms'
    '&field=title'
    '&format=json'
    '&limit=all'
)
