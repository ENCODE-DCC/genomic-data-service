PROJECTS = [
    {
        'id': 'ENCODE',
        'name': 'ENCODE: Encyclopedia of DNA Elements',
        'description': 'The Encyclopedia of DNA Elements (ENCODE) Consortium is an international collaboration of research groups funded by the National Human Genome Research Institute (NHGRI). The goal of ENCODE is to build a comprehensive parts list of functional elements in the human genome, including elements that act at the protein and RNA levels, and regulatory elements that control cells and circumstances in which a gene is active. ENCODE investigators employ a variety of assays and methods to identify functional elements. The discovery and annotation of gene elements is accomplished primarily by sequencing a diverse range of RNA sources, comparative genomics, integrative bioinformatic methods, and human curation. Regulatory elements are typically investigated through DNA hypersensitivity assays, assays of DNA methylation, and immunoprecipitation (IP) of proteins that interact with DNA and RNA, i.e., modified histones, transcription factors, chromatin regulators, and RNA-binding proteins, followed by sequencing.',
        'url': 'https://www.encodeproject.org',
    }
]


BASE_SEARCH_URL = 'https://www.encodeproject.org/search/'


DATASET_FILTERS = [
    ('type', 'Experiment'),
    ('status', 'released'),
    ('assay_title', 'polyA plus RNA-seq'),
    ('assay_title', 'total RNA-seq'),
    ('assay_title', 'polyA minus RNA-seq'),
    ('replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens'),
    ('replicates.library.biosample.donor.organism.scientific_name', 'Mus musculus'),
    ('assembly', 'GRCh38'),
    ('assembly', 'mm10'),
    ('files.file_type', 'tsv'),
    ('format', 'json'),
    ('frame', 'object'),
    ('field', 'accession'),
    ('field', 'assay_term_name'),
    ('field', 'assay_title'),
    ('field', 'assembly'),
    ('field', 'award'),
    ('field', 'biosample_ontology'),
    ('field', 'biosample_summary'),
    ('field', 'date_created'),
    ('field', 'description'),
    ('field', 'files'),
    ('field', 'lab'),
    ('field', 'replicates'),
    ('field', 'status'),
]


DATASET_FROM_TO_FIELD_MAP = {
    'accession': 'id',
}
