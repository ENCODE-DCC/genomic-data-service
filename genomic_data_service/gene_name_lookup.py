import requests


def gene_name_lookup(ensemblId):
    endpoint = "https://www.encodeproject.org/search/?type=Gene&organism.scientific_name=Homo+sapiens&format=json"
    dbxrefs = "&dbxrefs=ENSEMBL:" + ensemblId
    endpoint = endpoint + dbxrefs
    gene = requests.get(endpoint).json()["@graph"]
    if gene:
        return gene[0]["symbol"]
    else:
        return None
