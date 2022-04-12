import requests
import pickle


endpoint = "https://www.encodeproject.org/search/?type=Gene&organism.scientific_name=Homo+sapiens&format=json&limit=all"
genes = requests.get(endpoint).json()["@graph"]
gene_dict = {}

duplication_count = 0
id_count = 0
for gene in genes:
    dbxrefs = gene["dbxrefs"]
    gene_name = gene["symbol"]
    for ref in dbxrefs:
        if ref.startswith("ENSEMBL"):
            ensemblId = ref.split(":")[-1]
            if ensemblId not in gene_dict:
                gene_dict[ensemblId] = gene_name
                id_count += 1
            else:
                print("duplicated ensemblId:", gene_name, ensemblId)
                duplication_count += 1
            break

with open("gene_lookup.pickle", "wb") as myFile:
    pickle.dump(gene_dict, myFile)
