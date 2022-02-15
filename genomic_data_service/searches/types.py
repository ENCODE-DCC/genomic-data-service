types = [
    {
        "name": "RNAExpression",
        "item_type": "rna-expression",
        "schema": {
            "title": "RNAExpression",
            "description": "Schema for RNA-seq expression",
            "properties": {
                "uuid": {
                    "title": "UUID",
                },
                "expression": {
                    "type": "object",
                    "properties": {
                        "gene_id": {"title": "Gene ID", "type": "string"},
                        "transcript_ids": {"title": "Transcript ID", "type": "string"},
                        "tpm": {"title": "TPM", "type": "float"},
                        "fpkm": {"title": "FPKM", "type": "float"},
                    },
                },
                "file": {
                    "type": "object",
                    "properties": {
                        "@id": {"type": "string"},
                        "assay_title": {"title": "Assay title", "type": "string"},
                        "assembly": {"title": "Assembly", "type": "string"},
                        "biosample_ontology": {
                            "type": "object",
                            "properties": {
                                "organ_slims": {"type": "string"},
                                "term_name": {"type": "string"},
                                "synonyms": {"type": "string"},
                                "name": {"type": "string"},
                                "term_id": {"type": "string"},
                                "classification": {"type": "string"},
                            },
                        },
                        "dataset": {"type": "string"},
                        "donors": {"type": "string"},
                        "genome_annotation": {"type": "string"},
                    },
                },
                "dataset": {
                    "type": "object",
                    "properties": {
                        "@id": {"type": "string"},
                        "biosample_summary": {"type": "string"},
                        "replicates": {
                            "type": "object",
                            "properties": {
                                "library": {
                                    "type": "object",
                                    "properties": {
                                        "biosample": {
                                            "type": "object",
                                            "properties": {
                                                "age_units": {"type": "string"},
                                                "sex": {"type": "string"},
                                                "age": {"type": "string"},
                                                "donor": {
                                                    "type": "object",
                                                    "properties": {
                                                        "organism": {
                                                            "type": "object",
                                                            "properties": {
                                                                "scientific_name": {
                                                                    "type": "string"
                                                                }
                                                            },
                                                        }
                                                    },
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                        },
                    },
                },
                "gene": {
                    "type": "object",
                    "properties": {
                        "geneid": {"type": "string"},
                        "symbol": {"type": "string"},
                        "name": {"type": "string"},
                        "synonyms": {"type": "string"},
                        "@id": {"type": "string"},
                        "title": {"type": "string"},
                    },
                },
                "@id": {
                    "title": "ID",
                    "type": "string",
                },
                "@type": {
                    "title": "Type",
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "columns": {
                "expression.gene_id": {"title": "Feature ID"},
                "expression.tpm": {"title": "TPM"},
                "expression.fpkm": {"title": "FPKM"},
                "gene.symbol": {"title": "Gene symbol"},
                "gene.name": {"title": "Gene name"},
                "gene.title": {"title": "Gene title"},
                "file.biosample_ontology.term_name": {"title": "Biosample term name"},
                "file.assay_title": {"title": "Assay title"},
                "file.assembly": {"title": "Assembly"},
                "file.biosample_ontology.classification": {
                    "title": "Biosample classification"
                },
                "file.biosample_ontology.organ_slims": {"title": "Biosample organ"},
                "dataset.replicates.library.biosample.sex": {"title": "Biosample sex"},
                "dataset.replicates.library.biosample.donor.organism.scientific_name": {
                    "title": "Organism"
                },
                "dataset.biosample_summary": {"title": "Biosample summary"},
                "file.genome_annotation": {"title": "Genome annotation"},
                "file.donors": {"title": "Donors"},
                "file.@id": {"title": "File"},
                "dataset.@id": {"title": "Experiment"},
            },
            "facets": {
                "file.assay_title": {"title": "Assay title", "open_on_load": True},
                "file.biosample_ontology.classification": {
                    "title": "Biosample classification",
                    "open_on_load": True,
                },
                "file.biosample_ontology.term_name": {
                    "title": "Biosample term name",
                    "open_on_load": True,
                    "type": "typeahead",
                    "length": "long",
                },
                "file.assembly": {"title": "Assembly", "open_on_load": True},
                "dataset.replicates.library.biosample.donor.organism.scientific_name": {
                    "title": "Organism",
                    "open_on_load": True,
                },
                "dataset.replicates.library.biosample.sex": {"title": "Biosample sex"},
            },
        },
    }
]
