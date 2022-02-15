import csv
import os
import requests


def make_tsv_reader(iterable):
    return csv.reader(iterable, delimiter="\t", quotechar='"')


def iterate_response_by_row(response):
    return (row.decode("utf-8") for row in response.iter_lines())


def remote_tsv_iterable(url):
    with requests.get(url, stream=True) as response:
        iterable_response = iterate_response_by_row(response)
        for line in make_tsv_reader(iterable_response):
            yield line


def local_tsv_iterable(path):
    with open(path) as file_:
        for line in make_tsv_reader(file_):
            yield line


def save_file(remote_path, local_path):
    response = requests.get(remote_path)
    with open(local_path, "wb") as file_:
        file_.write(response.content)


def maybe_save_file(remote_path, local_path):
    if not os.path.exists(local_path):
        save_file(remote_path, local_path)
