from genomic_data_service import app
from flask import request


OPTIONAL_PARAMS = [
    'annotation',
    'cart',
    'datastore',
    'debug',
    'field',
    'filterresponse',
    'format',
    'frame',
    'from',
    'genome',
    'limit',
    'mode',
    'referrer',
    'region',
    'remove',
    'sort',
    'type',
    'config',
]


FREE_TEXT_QUERIES = [
    'advancedQuery',
    'searchTerm',
]


RESERVED_KEYS = NOT_FILTERS = OPTIONAL_PARAMS + FREE_TEXT_QUERIES

types = [
    {
        'name': 'RNAExpression',
        'item_type': 'rna-expression',
        'schema': {
            'title': 'RNAExpression',
            'description': 'Schema for RNA-seq expression',
            'properties': {
                'uuid': {
                    'title': 'UUID',
                    
                },
                'expression': {
                    'type': 'object',
                    'properties': {
                        'gene_id': {
                            'title': 'Gene ID',
                            'type': 'string'
                        },
                        'transcript_ids': {
                                'title': 'Transcript ID',
                                'type': 'string'
                            },
                            'tpm': {
                                'title': 'TPM',
                                'type': 'float'
                            },
                            'fpkm': {
                                'title': 'FPKM',
                                'type': 'float'
                            }
                        }
                    },
                    'file': {
                        'type': 'object',
                        'properties': {
                            '@id': {
                                'type': 'string'
                            },
                            'assay_title': {
                                'title': 'Assay title',
                                'type': 'string'
                            },
                            'assembly': {
                                'title': 'Assembly',
                                'type': 'string'
                            },
                            'biosample_ontology': {
                                'type': 'object',
                                'properties': {
                                    'organ_slims': {
                                        'type': 'string'
                                    },
                                    'term_name': {
                                        'type': 'string'
                                    },
                                    'synonyms': {
                                        'type': 'string'
                                    },
                                    'name': {
                                        'type': 'string'
                                    },
                                    'term_id': {
                                        'type': 'string'
                                    },
                                    'classification': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'dataset': {
                                'type': 'string'
                            },
                            'donors': {
                                'type': 'string'
                            },
                            'genome_annotation': {
                                'type': 'string'
                            }
                        }
                    },
                    'dataset': {
                        'type': 'object',
                        'properties': {
                            '@id': {
                                'type': 'string'
                            },
                            'biosample_summary': {
                                'type': 'string'
                            },
                            'replicates': {
                                'type': 'object',
                                'properties': {
                                    'library': {
                                        'type': 'object',
                                        'properties': {
                                            'biosample': {
                                                'type': 'object',
                                                'properties': {
                                                    'age_units': {
                                                        'type': 'string'
                                                    },
                                                    'sex': {
                                                        'type': 'string'
                                                    },
                                                    'age': {
                                                        'type': 'string'
                                                    },
                                                    'donor': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'organism': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'scientific_name': {
                                                                        'type': 'string'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'gene': {
                        'type': 'object',
                        'properties': {
                            'geneid': {
                                'type': 'string'
                            },
                            'symbol': {
                                'type': 'string'
                            },
                            'name': {
                                'type': 'string'
                            },
                            'synonyms': {
                                'type': 'string'
                            },
                            '@id': {
                                'type': 'string'
                            },
                            'title': {
                                'type': 'string'
                            }
                        }
                    },
                    '@id': {
                        'title': 'ID',
                        'type': 'string',
                    },
                    '@type': {
                        'title': 'Type',
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                    },
                    'expression_id': {
                        'title': 'Expression ID',
                        'type': 'string'
                    }
                },
                'columns': {
                    'expression.gene_id': {
                        'title': 'Feature ID'
                    },
                    'expression.tpm': {
                        'title': 'TPM'
                    },
                    'expression.fpkm': {
                        'title': 'FPKM'
                    },
                    'gene.symbol': {
                        'title': 'Gene symbol'
                    },
                    'gene.name': {
                        'title': 'Gene name'
                    },
                    'gene.title': {
                        'title': 'Gene title'
                    },
                    'file.biosample_ontology.term_name': {
                        'title': 'Biosample term name'
                    },
                    'file.assay_title': {
                        'title': 'Assay title'
                    },
                    'file.assembly': {
                        'title': 'Assembly'
                    },
                    'file.biosample_ontology.classification': {
                        'title': 'Biosample classification'
                    },
                    'file.biosample_ontology.organ_slims': {
                        'title': 'Biosample organ'
                    },
                    'dataset.replicates.library.biosample.sex': {
                        'title': 'Biosample sex'
                    },
                    'dataset.replicates.library.biosample.donor.organism.scientific_name': {
                        'title': 'Organism'
                    },
                    'dataset.biosample_summary': {
                        'title': 'Biosample summary'
                    },
                    'expression_id': {
                        'title': 'Expression ID'
                    },
                    'file.genome_annotation': {
                        'title': 'Genome annotation'
                    },
                    'file.donors': {
                        'title': 'Donors'
                    },
                    'file.@id': {
                        'title': 'File'
                    },
                    'dataset.@id': {
                        'title': 'Experiment'
                    }
                },
                'facets': {
                    'file.assay_title': {
                        'title': 'Assay title',
                        'open_on_load': True
                    },
                    'file.biosample_ontology.classification': {
                        'title': 'Biosample classification',
                        'open_on_load': True
                    },
                    'file.biosample_ontology.term_name': {
                        'title': 'Biosample term name',
                        'open_on_load': True,
                        'type': 'typeahead',
                        'length': 'long'
                    },
                    'gene.symbol': {
                        'title': 'Gene symbol',
                        'open_on_load': True,
                        'type': 'typeahead',
                        'length': 'long'
                    },
                    'file.assembly': {
                        'title': 'Assembly',
                        'open_on_load': True
                    },
                    'dataset.replicates.library.biosample.donor.organism.scientific_name': {
                        'title': 'Organism',
                        'open_on_load': True
                    },
                    'dataset.replicates.library.biosample.sex': {
                        'title': 'Biosample sex'
                    }
                },
            }
        }
]

configs = [
    {
        'name': type_['name'],
        **type_.get('schema', {}),
    }
    for type_ in types
]

def make_registry(types, configs):
    from snosearch.adapters.types import register_type_from_dict
    from snosearch.adapters.configs import register_search_config_from_dict
    from snosearch.configs import SearchConfigRegistry
    from snosearch.interfaces import TYPES
    from snosearch.interfaces import ELASTIC_SEARCH
    from snosearch.interfaces import SEARCH_CONFIG
    registry = {}
    type_registry = {}
    for type_dict in types:
        register_type_from_dict(type_registry, type_dict)
    registry[TYPES] = type_registry
    registry[ELASTIC_SEARCH] = None
    config_registry = SearchConfigRegistry()
    for config_dict in configs:
        register_search_config_from_dict(config_registry, config_dict)
    registry[SEARCH_CONFIG] = config_registry
    return registry


@app.route('/rnaget-search/', methods=['GET'])
def rnaget_search():
    from elasticsearch import Elasticsearch
    es = Elasticsearch('127.0.0.1:9202')

    from snosearch.fields import BasicSearchResponseField
    from snosearch.fields import DebugQueryResponseField
    from snosearch.parsers import ParamsParser
    from snosearch.responses import FieldedInMemoryResponse
    from snosearch.adapters.flask.requests import RequestAdapter
    from flask import make_response

    from flask import stream_with_context
    
    registry = make_registry(types, configs)
    wrapped_request = RequestAdapter(request)
    wrapped_request.registry = registry
    wrapped_request.response = make_response()
    
    fr = FieldedInMemoryResponse(
        _meta={
            'params_parser': ParamsParser(
                wrapped_request
            )
        },
        response_fields=[
            BasicSearchResponseField(
                client=es,
                default_item_types=[
                    'RNAExpression',
                ],
                reserved_keys=RESERVED_KEYS,
            ),
            DebugQueryResponseField(),
        ]
    )
    return fr.render()
