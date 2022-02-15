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


@pytest.fixture(scope='session')
def elasticsearch_client(host='127.0.0.1', port=9202):
    from elasticsearch import Elasticsearch
    with start_elasticsearch(host=host, port=port) as process:
        yield Elasticsearch(
            [f'{host}:{port}']
        )
