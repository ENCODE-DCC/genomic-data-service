MATCH_ALL = {
    'query': {
        'match_all': {}
    }
}


INDEX_SETTINGS =  {
    'index.max_result_window': 99999,
    'index.mapping.total_fields.limit': 5000,
    'index.number_of_shards': 1,
    'index.number_of_replicas': 0,
    'analysis': {
        'filter': {
            'substring': {
                'type': 'edge_ngram',
                'min_gram': 1,
                'max_gram': 33
            },
            'english_stop': {
                'type': 'stop',
                'stopwords': '_english_'
            },
            'english_stemmer': {
                'type': 'stemmer',
                'language': 'english'
            },
            'english_possessive_stemmer': {
                'type': 'stemmer',
                'language': 'possessive_english'
            },
            'delimiter': {
                'type': 'word_delimiter',
                'catenate_all': True,
                'preserve_original': True,
                'stem_english_possessive': True,
                'split_on_numerics': False
            }
        },
        'analyzer': {
            'default': {
                'type': 'custom',
                'tokenizer': 'whitespace',
                'char_filter': 'html_strip',
                'filter': [
                    'english_possessive_stemmer',
                    'lowercase',
                    'english_stop',
                    'english_stemmer',
                    'asciifolding',
                    'delimiter'
                ]
            },
            'analyzer_when_indexing': {
                'type': 'custom',
                'tokenizer': 'whitespace',
                'char_filter': 'html_strip',
                'filter': [
                    'english_possessive_stemmer',
                    'lowercase',
                    'english_stop',
                    'english_stemmer',
                    'asciifolding',
                    'delimiter',
                    'substring'
                ]
            },
            'analyzer_when_searching': {
                'type': 'custom',
                'tokenizer': 'whitespace',
                'filter': [
                    'english_possessive_stemmer',
                    'lowercase',
                    'english_stop',
                    'english_stemmer',
                    'asciifolding',
                    'delimiter'
                ]
            }
        }
    }
}


EXPRESSION_MAPPING = {
    'settings': INDEX_SETTINGS,
    'mappings': {
        'rna-expression': {
            '_all': {
                'enabled': True,
                'analyzer': 'analyzer_when_indexing',
                'search_analyzer': 'analyzer_when_searching'
            },
            'properties': {
                'principals_allowed': {
                    'include_in_all': False,
                    'properties': {
                        'view': {
                            'type': 'keyword'
                        }
                    },
                },
                'embedded': {
                    'include_in_all': False,
                    'properties': {
                        'expression': {
                            'properties': {
                                'gene_id': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'transcript_ids': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'tpm': {
                                    'type': 'float'
                                },
                                'fpkm': {
                                    'type': 'float'
                                }
                            }
                        },
                        'file': {
                            'properties': {
                                '@id': {
                                    'type': 'keyword'
                                },
                                'assay_title': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'assembly': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'biosample_ontology': {
                                    'properties': {
                                        'organ_slims': {
                                            'type': 'keyword',
                                            'include_in_all': True
                                        },
                                        'term_name': {
                                            'type': 'keyword',
                                            'include_in_all': True
                                        },
                                        'synonyms': {
                                            'type': 'keyword',
                                            'include_in_all': True
                                        },
                                        'name': {
                                            'type': 'keyword',
                                            'include_in_all': True
                                        },
                                        'term_id': {
                                            'type': 'keyword',
                                            'include_in_all': True
                                        },
                                        'classification': {
                                            'type': 'keyword',
                                            'include_in_all': True
                                        }
                                    }
                                },
                                'dataset': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'donors': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'genome_annotation': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                }
                            }
                        },
                        'dataset': {
                            'properties': {
                                '@id': {
                                    'type': 'keyword'
                                },
                                'biosample_summary': {
                                    'type': 'text',
                                    'include_in_all': True
                                },
                                'replicates': {
                                    'properties': {
                                        'library': {
                                            'properties': {
                                                'biosample': {
                                                    'properties': {
                                                        'age_units': {
                                                            'type': 'keyword',
                                                            'include_in_all': True
                                                        },
                                                        'sex': {
                                                            'type': 'keyword',
                                                            'include_in_all': True
                                                        },
                                                        'age': {
                                                            'type': 'long',
                                                            'include_in_all': True
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
                            'properties': {
                                'geneid': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'symbol': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'name': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'synonyms': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                '@id':  {
                                    'type': 'keyword',
                                    'include_in_all': True
                                },
                                'title': {
                                    'type': 'keyword',
                                    'include_in_all': True
                                }
                            }
                        },
                        '@id': {
                            'type': 'keyword',
                            'include_in_all': True
                        },
                        '@type': {
                            'type': 'keyword'
                        },
                        'expression_id': {
                            'type': 'keyword'
                        },
                        'principals_allowed.view': {
                            'type': 'keyword'
                        }
                    }
                }
            }
        }
    }
}
