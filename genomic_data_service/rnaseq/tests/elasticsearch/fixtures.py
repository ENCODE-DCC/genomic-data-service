import pytest

from contextlib import contextmanager


@contextmanager
def start_elasticsearch(host='127.0.0.1', port=9202):
    import io
    import os
    import shutil
    import subprocess
    import tempfile
    data_directory = tempfile.mkdtemp()
    command = [
        'elasticsearch',
        f'-Enetwork.host={host}',
        f'-Ehttp.port={port}',
        f'-Epath.data={os.path.join(data_directory, "data")}',
        f'-Epath.logs={os.path.join(data_directory, "logs")}',
        f'-Epath.conf=./genomic_data_service/rnaseq/tests/elasticsearch/conf',
    ]
    process = subprocess.Popen(
        command,
        close_fds=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for line in io.TextIOWrapper(
            process.stdout,
            encoding="utf-8"
    ):
        print(line)
        if 'started' in line:
            print('ES up and running')
            break
    try:
        print('yielding ES')
        yield process
    finally:
        print('cleaning up ES')
        process.terminate()
        process.wait()
        shutil.rmtree(data_directory)


mapping = {
    "mappings": {
        "expression": {
            "properties": {
                "principals_allowed.view": {
                    "type": "keyword"                    
                },
                "embedded.@id": {
                    "type": "keyword"
                },
                "embedded.@type": {
                    "type": "keyword"
                },
                "embedded.annotation": {
                    "type": "keyword"
                },
                "embedded.assayType": {
                    "type": "keyword"
                },
                "embedded.biosample_classification": {
                    "type": "keyword"
                },
                "embedded.biosample_organ": {
                    "type": "keyword"
                },
                "embedded.biosample_sex": {
                    "type": "keyword"
                },
                "embedded.biosample_summary": {
                    "type": "keyword"
                },
                "embedded.biosample_system": {
                    "type": "keyword"
                },
                "embedded.biosample_term_name": {
                    "type": "keyword"
                },
                "embedded.encodeID": {
                    "type": "keyword"
                },
                "embedded.expressionID": {
                    "type": "keyword"
                },
                "embedded.featureID": {
                    "type": "keyword"
                },
                "embedded.gene_name": {
                    "type": "keyword"
                },
                "embedded.gene_symbol": {
                    "type": "keyword"
                },
                "embedded.libraryPrepProtocol": {
                    "type": "keyword"
                },
                "embedded.samplePrepProtocol": {
                    "type": "keyword"
                },
                "embedded.tpm": {
                    "type": "float"
                }
            }
        }
    }
}


data = [
        {
            "annotation": "GRCh38",
            "assayType": "shRNA knockdown followed by RNA-seq",
            "biosample_classification": "cell line",
            "biosample_organ": "exocrine gland, epithelium, liver, endocrine gland",
            "biosample_sex": "male",
            "biosample_summary": "Homo sapiens HepG2 cell line expressing RNAi targeting GNB2L1",
            "biosample_system": "digestive system, endocrine system, exocrine system",
            "biosample_term_name": "HepG2",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF007FIZ",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR116YMU",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR116YMU",
            "tpm": "70.00"
        },
        {
            "annotation": "GRCh38",
            "assayType": "CRISPR genome editing followed by RNA-seq",
            "biosample_classification": "cell line",
            "biosample_organ": "blood, bodily fluid",
            "biosample_sex": "female",
            "biosample_summary": "Homo sapiens K562 cell line genetically modified (deletion) using CRISPR targeting FXR2",
            "biosample_system": "immune system",
            "biosample_term_name": "K562",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF006ECV",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR376GHG",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR376GHG",
            "tpm": "38.10"
        },
        {
            "annotation": "GRCh38",
            "assayType": "polyA plus RNA-seq",
            "biosample_classification": "tissue",
            "biosample_organ": "musculature of body, limb",
            "biosample_sex": "unknown",
            "biosample_summary": "Homo sapiens embryo (101 days) muscle of arm tissue",
            "biosample_system": "musculature",
            "biosample_term_name": "muscle of arm",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF007LRI",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR677MYO",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR677MYO",
            "tpm": "1.40"
        },
    ]


index_and_doc_type = {
    '_index': 'expression',
    '_type': 'expression',
    'principals_allowed.view': ["system.Everyone"]
}


def transform_data(data):
    for datum in data:
        datum['@type'] = ['Expression', 'Item']
        datum['@id'] = f"/expressions/{datum['expressionID']}/{datum['featureID']}/"
        datum['tpm'] = float(datum['tpm'])
        new_data = {
            'embedded': datum
        }
        new_data.update(index_and_doc_type)
        yield new_data


data = [
    d
    for d in transform_data(data)
]


def load_data(es):
     from elasticsearch import helpers
     es.indices.create(index='expression')
     helpers.bulk(es, data, chunk_size=1000, request_timeout=200)
     es.indices.refresh(index='expression')


@pytest.fixture(scope='session')
def elasticsearch_with_data(host='127.0.0.1', port=9202):
    from elasticsearch import Elasticsearch
    with start_elasticsearch(host=host, port=port) as process:
        es = Elasticsearch(
            [f'{host}:{port}']
        )
        load_data(es)
