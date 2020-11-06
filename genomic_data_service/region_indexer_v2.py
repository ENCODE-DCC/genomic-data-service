from elasticsearch import Elasticsearch

from genomic_data_service import app
from genomic_data_service.region_indexer_task import index_file

from sqlalchemy import create_engine, Column, Integer, String, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql.expression import cast

es = Elasticsearch(port=app.config['ES_PORT'], hosts=app.config['ES_HOSTS'])

engine = create_engine("postgresql://postgres@:5432/postgres?host=/tmp/snovault/pgdata")
Base = declarative_base()
Session = sessionmaker(bind=engine)

session = Session()

REGULOME_ALLOWED_STATUSES = ['released', 'archived']
REGULOME_SUPPORTED_ASSEMBLIES = ['hg19', 'GRCh38']
REGULOME_COLLECTION_TYPES = ['assay_term_name', 'annotation_type', 'reference_type']
REGULOME_DATASET_TYPES = ['experiment', 'annotation', 'reference']
REGULOME_REGION_REQUIREMENTS = {
    'ChIP-seq': {
        'output_type': ['optimal idr thresholded peaks'],
        'file_format': ['bed']
    },
    'binding sites': {
        'output_type': ['curated binding sites'],
        'file_format': ['bed']
    },
    'DNase-seq': {
        'output_type': ['peaks'],
        'file_type': ['bed narrowPeak'],
        'file_format': ['bed']
    },
    'FAIRE-seq': {
        'file_type': ['bed narrowPeak'],
        'file_format': ['bed']
    },
    'chromatin state': {
        'file_format': ['bed']
    },
    'PWMs': {
        'output_type': ['PWMs'],
        'file_format': ['bed']
    },
    'Footprints': {
        'output_type': ['Footprints'],
        'file_format': ['bed']
    },
    'eQTLs': {
        'file_format': ['bed']
    },
    'dsQTLs': {
        'file_format': ['bed']
    },
    'curated SNVs': {
        'output_type': ['curated SNVs'],
        'file_format': ['bed']
    },
    'index': {
        'output_type': ['variant calls'],
        'file_format': ['bed']
    }
}


class Resources(Base):
    __tablename__ = 'resources'

    rid = Column(String, primary_key=True)
    item_type = Column(String)

    
class Propsheets(Base):
    __tablename__ = 'propsheets'

    sid = Column(Integer, primary_key=True)
    rid = Column(String)
    name = Column(String)
    properties = Column(JSON)
    tid = Column(UUID(as_uuid=True))


class CurrentPropsheets(Base):
    __tablename__ = 'current_propsheets'

    sid = Column(Integer, primary_key=True)
    rid = Column(String)
    name = Column(String)


def fetch_active_snovault_record(uuid):
    curent_propsheet, item, resource = session.query(CurrentPropsheets, Propsheets, Resources).filter(CurrentPropsheets.sid == Propsheets.sid).filter(Propsheets.rid == Resources.rid).filter(CurrentPropsheets.rid == uuid).first() or (None, None, None)

    return item.properties, resource and resource.item_type

    
def fetch_dataset(dataset_id):
    return fetch_active_snovault_record(dataset_id)


def fetch_bed_files():
    file_rids = session.query(Resources.rid).filter(Resources.item_type == 'file').order_by(Resources.rid).all()

    return session.query(Propsheets).filter(text("properties->>'file_format' in ('bed', 'narrowPeak', 'bed narrowPeak')")).filter(Propsheets.rid.in_(file_rids)).all()


def fetch_target(target_id):
    target, target_type = fetch_active_snovault_record(target_id)

    target['uuid'] = str(target_id)
    target['@id'] = '/' + target_type + '/' + target.get('name', target_id) + '/'

    genes = []
    for gene_id in target.get('genes', []):
        gene_obj = {}

        gene, gene_type = fetch_active_snovault_record(gene_id)

        if not gene:
            next

        genes.append({
            'uuid': gene_id,
            'symbol': gene.get('symbol', None)
        })
    target['genes'] = genes
    
    return target

def fetch_biosample_ontology(dataset):
    ontology_id = dataset.get('biosample_ontology')
    if ontology_id:
        biosample_ontology, ontology_type = fetch_active_snovault_record(ontology_id)
        if biosample_ontology:
            biosample_ontology['uuid'] = ontology_id
            return biosample_ontology
    return None


def regulome_collection_type(dataset):
    for prop in REGULOME_COLLECTION_TYPES:
        if prop in dataset:
            return dataset[prop]
    return None


def check_embedded_targets(dataset):
    target = dataset.get('target')

    if target is not None:
        if not isinstance(target, str):
            return target
        else:
            try:
                return fetch_target(target)
            except Exception:
                print("Target " + target + " is not found for: " + dataset['@id'])
                return None
    else:
        targets = dataset.get('targets', [])
        if len(targets) > 0:
            if isinstance(targets[0], dict):
                return targets
            target_objects = []
            for target in targets:
                if isinstance(targets[0], str):
                    try:
                        target_objects.append(fetch_target(target))
                    except Exception:
                        print("Target " + target + " is not found for: " + dataset['@id'])
            return target_objects

    return None


def file_dataset_allowed_to_index(file):
    uuid = str(file.rid)
    properties = file.properties

    if properties.get('href') is None:
        print('File ' + uuid + ' refused because href is null')
        return None

    if properties.get('status') not in REGULOME_ALLOWED_STATUSES:
        print('File ' + uuid + ' refused because status is ' + properties.get('status'))
        return None

    if properties.get('assembly', 'unkown') not in REGULOME_SUPPORTED_ASSEMBLIES:
        print('File ' + uuid + ' refused because assembly is not accepted: ' + properties.get('assembly'))
        return None

    dataset_id = properties.get('dataset')

    if dataset_id is None:
        print('File ' + uuid + ' has no dataset id')
        return None

    dataset, dataset_type = fetch_dataset(dataset_id)

    if dataset is None or dataset_type is None:
        print('File ' + uuid + ' dataset and/or resource not found ' + dataset_id)
        return None

    if dataset_type not in REGULOME_DATASET_TYPES:
        print('File ' + uuid + ' dataset type not allowed: ' + dataset_type)
        return None

    dataset_collection_type = None
    for collection_type in REGULOME_COLLECTION_TYPES:
        if collection_type in dataset:
            dataset_collection_type = dataset.get(collection_type, None)
            if dataset_collection_type is not None:
                break

    if dataset_collection_type is None:
        print('File ' + uuid + ' dataset has no required collection type.')
        return None
    
    if dataset_collection_type not in REGULOME_REGION_REQUIREMENTS:
        print('File ' + uuid + ' collection type not allowed: ' + collection_type)
        return None

    requirements = REGULOME_REGION_REQUIREMENTS[dataset_collection_type]
    for key, values in requirements.items():
        if properties.get(key) not in values:
            print('File ' + uuid + ' dataset collection type does not satisfy all requirements')
            return None        

    # REG-14 special case for indexing dbSNP v153 only
    if dataset_collection_type == 'index' and (
        'RegulomeDB' not in dataset.get('internal_tags', [])
        or dataset['status'] != 'released'
    ):
        print('File ' + uuid + ' dataset collection type index has no Regulome tag')
        return None
    
    # REG-186 special case for chromatin state data since new data is not
    # compatible with current regulome model.
    if dataset_collection_type == 'chromatin state' and ('RegulomeDB' not in dataset.get('internal_tags', [])):
        print('File ' + uuid + ' dataset collection type chromatin has no Regulome tag')
        return None

    dataset['@id'] = '/' + dataset_type + '/' + dataset['accession'] + '/' # PEDRO TODO: refactor out
    dataset['@type'] = [dataset_type] # TODO: this is incomplete and have to export from snovault somehow
    dataset['uuid'] = str(dataset_id)
    target = check_embedded_targets(dataset)
    if target is not None:
        dataset['target'] = target
    biosample_ontology = fetch_biosample_ontology(dataset)
    if biosample_ontology is not None:
        dataset['biosample_ontology'] = biosample_ontology

    return dataset


def index_regions():
    files = fetch_bed_files()

    num_files_indexed = 0

    for f in files:
        dataset = file_dataset_allowed_to_index(f)
        if dataset:
            file_properties = f.properties
            file_properties['@id'] = '/files/' + file_properties['accession'] + '/' # PEDRO TODO: refactor out

            index_file(uuid=str(f.rid), file_properties=f.properties, dataset=dataset)

            num_files_indexed += 1

    print(str(num_files_indexed) + " files scheduled for indexing.")


if __name__ == "__main__":
    index_regions()
