from genomic_data_service.rnaseq.rnaget.constants import DATASET_FROM_TO_FIELD_MAP


def map_fields(item, from_to_field_map):
    new_item = {}
    for from_field, to_field in from_to_field_map.items():
        value = item.get(from_field)
        if value:
            new_item[to_field] = value
    filtered_item = {
        k: v
        for k, v in item.items()
        if k not in from_to_field_map
    }
    return {
        **new_item,
        **filtered_item,
    }


def convert_study_fields(study):
    return map_fields(study, DATASET_FROM_TO_FIELD_MAP)


def convert_facet_to_filter(facet):
    return {
        'filter': facet.get('field'),
        'description': facet.get('title'),
        'values': [
            value.get('key')
            for value in facet.get('terms', [])
        ],
    }
