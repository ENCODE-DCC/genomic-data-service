from flask import abort
from flask import Blueprint
from flask import jsonify


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
