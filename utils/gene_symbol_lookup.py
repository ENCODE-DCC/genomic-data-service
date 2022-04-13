import requests
import pickle


def get_gene_symbol(ensembl_id):
    url = (
        "https://rest.ensembl.org/lookup/id/"
        + ensembl_id
        + "?content-type=application/json"
    )
    data = requests.get(url).json()
    gene_symbol = data.get("display_name")
    return gene_symbol


def get_ensembl_id(gene_symbol):
    updated_ensembl_id = None
    url = (
        "https://rest.ensembl.org/xrefs/symbol/homo_sapiens/"
        + gene_symbol
        + "?content-type=application/json"
    )
    data = requests.get(url).json()
    if data:
        for item in data:
            if item["id"].startswith("ENSG"):
                updated_ensembl_id = item["id"]
                break
    return updated_ensembl_id


def main():
    endpoint = "https://www.encodeproject.org/search/?type=Gene&organism.scientific_name=Homo+sapiens&format=json&limit=all"
    genes = requests.get(endpoint).json()["@graph"]
    gene_symbol_dict = {}
    duplicate_ensembl_ids = []
    for gene in genes:
        dbxrefs = gene["dbxrefs"]
        gene_symbol = gene["symbol"]
        for ref in dbxrefs:
            if ref.startswith("ENSEMBL"):
                ensembl_id = ref.split(":")[-1]
                if ensembl_id in gene_symbol_dict:
                    duplicate_ensembl_ids.append(ensembl_id)
                else:
                    gene_symbol_dict[ensembl_id] = gene_symbol
                break
    # If there are more than one gene symbols for the same ensembl_id, get the gene symbol from ensembl.
    for ensembl_id in duplicate_ensembl_ids:
        gene_symbol = get_gene_symbol(ensembl_id)
        if gene_symbol:
            gene_symbol_dict[ensembl_id] = gene_symbol
        # if the ensembl is retired, get the updated ensembl id.
        else:
            gene_symbol = gene_symbol_dict[ensembl_id]
            updated_ensembl_id = get_ensembl_id(gene_symbol)                    
            updated_gene_symbol = get_gene_symbol(updated_ensembl_id)
            gene_symbol_dict[ensembl_id] = updated_gene_symbol
            gene_symbol_dict[updated_ensembl_id] = updated_gene_symbol

    with open("gene_lookup.pickle", "wb") as file:
        pickle.dump(gene_symbol_dict, file)

if __name__ == "__main__":
    main()
