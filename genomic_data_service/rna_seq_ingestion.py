from genomic_data_service import db
from genomic_data_service.models import Feature, Expression, File, Project, Study
import requests
import csv
import pickle
import json

import os.path
from os import path

from celery import Celery


celery_app = Celery('rna_seq_ingestion', broker='redis://localhost')


def extract_project(metadata):
    award = metadata['award']

    id = award['uuid']

    exists = Project.query.filter(Project.id == id).first()
    if exists:
        return exists

    return Project(
        id=id,
        version=award['schema_version'],
        name=award['project'],
        description=award.get('description')
    )


def extract_study(metadata, parent_project_id):    
    experiment = requests.get("https://www.encodeproject.org" + metadata['dataset'] + "?format=json")

    if experiment.status_code != 200:
        print("Failed to acquire metadata for " + metadata['dataset'])
        return None

    if 'genome_annotation' not in metadata:
        print("Genome annotation not found for " + metadata['dataset'] + ". Skipping...")
        return None

    experiment = experiment.json()
    genome = metadata['assembly'] + ' ' + metadata.get('genome_annotation', '')

    exists = Study.query.filter(Study.id == experiment['accession']).first()
    if exists:
        return exists

    return Study(
        id=experiment['accession'],
        name=experiment.get('description', 'Study ' + experiment['accession']),
        version=experiment['date_released'],
        description=experiment.get('description'),
        parent_project_id=parent_project_id,
        genome=genome
    )


def extract_file(metadata, study_id):
    if metadata['file_format'] not in File.ACCEPTED_FORMATS:
        print("Unprocessable file format " + metadata['file_format'] + " for " + metadata['href'])
        return None

    exists = File.query.filter(File.id == metadata['accession']).first()
    if exists:
        return exists

    return File(
        id=metadata['accession'],
        file_type=metadata['file_type'],
        url="https://encodeproject.org"+metadata['href'],
        version=metadata['date_created'],
        study_id=study_id,
        md5=metadata['md5sum'],
        assay=metadata['assay_term_name'],
        assembly=metadata['assembly'],
        assembly_version=metadata['genome_annotation']
    )


def fetch_reject_list():
    print("Fetching rejection list...")

    reject_list_url = "https://www.encodeproject.org/search/?type=File&status=released&output_type=gene+quantifications&assembly=mm10&assay_term_name!=single-cell+RNA+sequencing+assay&limit=all&format=json"

    reject_response = requests.get(reject_list_url).json()

    reject_accessions = set([])
    for item in reject_response['@graph']:
        reject_accessions.add(item['accession'])

    return reject_accessions
        

def get_all_accessions():
    pickle_filename = 'rna_seq_accessions.pickle'

    if path.exists(pickle_filename):
        return pickle.load(open(pickle_filename, 'rb'))

    reject_list = fetch_reject_list()

    print("Fetching files list...")
    gene_quantifications_list = "https://www.encodeproject.org/search/?type=File&status=released&output_type=gene+quantifications&assembly=GRCh38&limit=all&format=json"

    files_metadata = requests.get(gene_quantifications_list).json()

    accessions_to_process = set([])
    for entry in files_metadata['@graph']:
        if entry['accession'] not in reject_list:
            accessions_to_process.add(entry['accession'])

    with open(pickle_filename, 'wb') as output:
        pickle.dump(accessions_to_process, output)

    return accessions_to_process


@celery_app.task(bind=True, name='genomic_data_service.rna_seq_ingestion.process_accession', autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_accession(self, accession):
    print("Processing " + accession + " ...")
    metadata = requests.get("https://www.encodeproject.org/files/" + accession + "?format=json")

    if metadata.status_code != 200:
        print("Failed to acquire metadata for " + accession)
        return

    metadata = metadata.json()

    project = extract_project(metadata)
    study = extract_study(metadata, project.id)

    file = None
    if study:
        file = extract_file(metadata, study.id)

    for entry in [project, study, file]:
        if entry:
            db.session.add(entry)

    db.session.commit()


@celery_app.task(bind=True, name='genomic_data_service.rna_seq_ingestion.process_expressions', autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_expressions(self, file_id):
    file = File.query.filter(File.id == file_id).first()
    file.import_expressions()


def index_features_from_json(json_filename):
    transcript_maps = json.loads(open(json_filename, 'r').read())[0]

    for gene_id in transcript_maps:
        transcripts = transcript_maps[gene_id]
        for transcript in transcripts:
            feature = Feature(gene_id=gene_id, transcript_id=transcript)
            db.session.add(feature)
    db.session.commit()
    

def index_all_accessions():
    accessions = sorted(list(get_all_accessions()))

    for accession in accessions:
        process_accession.delay(accession)


def index_all_expressions():
    for file in File.query.all():
        process_expressions.delay(file.id)


if __name__ == "__main__":
    index_all_expressions()

