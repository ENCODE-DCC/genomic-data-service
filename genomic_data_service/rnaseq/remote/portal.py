import requests


def get_json(url):
    response = requests.get(url)
    return response.json()


class Portal:

    def __init__(self):
        pass

    def get_rna_seq_files(self):
        pass
