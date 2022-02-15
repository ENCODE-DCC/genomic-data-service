from genomic_data_service.searches.types import types

from snosearch.adapters.types import register_type_from_dict
from snosearch.adapters.configs import register_search_config_from_dict
from snosearch.configs import SearchConfigRegistry
from snosearch.interfaces import TYPES
from snosearch.interfaces import SEARCH_CONFIG


configs = [
    {
        "name": type_["name"],
        **type_.get("schema", {}),
    }
    for type_ in types
]


def make_registry(types, configs):
    registry = {}
    type_registry = {}
    for type_dict in types:
        register_type_from_dict(type_registry, type_dict)
    registry[TYPES] = type_registry
    config_registry = SearchConfigRegistry()
    for config_dict in configs:
        register_search_config_from_dict(config_registry, config_dict)
    registry[SEARCH_CONFIG] = config_registry
    return registry


def add_registry(app):
    app.registry = make_registry(types, configs)
