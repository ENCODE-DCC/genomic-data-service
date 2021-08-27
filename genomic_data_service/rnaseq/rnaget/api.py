from flask import abort
from flask import Blueprint
from flask import jsonify

from genomic_data_service.rnaseq.remote.portal import get_json
from genomic_data_service.rnaseq.remote.portal import Portal
from genomic_data_service.searches import make_search_request

from snosearch.parsers import QueryString


rnaget_api = Blueprint(
    'rnaget_api',
    __name__,
)


PROJECTS = [
    {
        'id': 'ENCODE',
        'name': 'ENCODE: Encyclopedia of DNA Elements',
        'description': 'The Encyclopedia of DNA Elements (ENCODE) Consortium is an international collaboration of research groups funded by the National Human Genome Research Institute (NHGRI). The goal of ENCODE is to build a comprehensive parts list of functional elements in the human genome, including elements that act at the protein and RNA levels, and regulatory elements that control cells and circumstances in which a gene is active. ENCODE investigators employ a variety of assays and methods to identify functional elements. The discovery and annotation of gene elements is accomplished primarily by sequencing a diverse range of RNA sources, comparative genomics, integrative bioinformatic methods, and human curation. Regulatory elements are typically investigated through DNA hypersensitivity assays, assays of DNA methylation, and immunoprecipitation (IP) of proteins that interact with DNA and RNA, i.e., modified histones, transcription factors, chromatin regulators, and RNA-binding proteins, followed by sequencing.',
        'url': 'https://www.encodeproject.org',
    }
]


BASE_SEARCH_URL = 'www.encodeproject.org/search/'


DATASET_FILTERS = [
    ('type', 'Experiment'),
    ('status', 'released'),
    ('assay_title', 'polyA plus RNA-seq'),
    ('assay_title', 'total RNA-seq'),
    ('assay_title', 'polyA minus RNA-seq'),
    ('replicates.library.biosample.donor.organism.scientific_name', 'Homo sapiens'),
    ('replicates.library.biosample.donor.organism.scientific_name', 'Mus musculus'),
    ('assembly', 'GRCh38'),
    ('assembly' 'mm10'),
    ('files.file_type', 'tsv'),
]


@rnaget_api.route('/projects', methods=['GET'])
def projects():
    return jsonify(PROJECTS)


@rnaget_api.route('/projects/<project_id>', methods=['GET'])
def project_id(project_id):
    projects = [
        project
        for project in PROJECTS
        if project['id'] == project_id
    ]
    if not projects:
        abort(404, 'Project not found')
    return jsonify(projects)


@rnaget_api.route('/projects/filters', methods=['GET'])
def project_filters():
    return jsonify([])


@app.route('/studies', methods=['GET'])
def studies():
    qs = QueryString(make_search_request())
    portal = Portal()
    base_url = Portal._get_dataset_url()
    
    version = request.args.get('version')
    page = request.args.get('page', 1, type=int)

    studies = Study.query

    if version:
        studies = studies.filter_by(version=version)

    studies = studies.paginate(page, Study.PER_PAGE, False)
    return jsonify([study.to_dict() for study in studies.items])


@app.route('/studies/<study_id>', methods=['GET'])
def studies_id(study_id):
    study = Study.query.filter_by(id=study_id).first_or_404(description="Study not found")

    return jsonify(study.to_dict())


@app.route('/studies/filters', methods=['GET'])
def study_filters():
    return jsonify(Study.FILTERS)
