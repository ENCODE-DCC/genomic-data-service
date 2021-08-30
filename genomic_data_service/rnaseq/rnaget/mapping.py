from genomic_data_service.rnaseq.rnaget.constants import DATASET_FROM_TO_FIELD_MAP
from genomic_data_service.rnaseq.rnaget.constants import EXPRESSION_IDS_MAP
from genomic_data_service.rnaseq.rnaget.constants import EXPRESSION_LIST_FILTERS_MAP


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


def convert_list_filters_to_expression_filters(qs):
    for list_filter, expression_filter in EXPRESSION_LIST_FILTERS_MAP.items():
        value = qs.get_one_value(
            params=qs.get_key_filters(
                key=list_filter
            )
        ) or ''
        values = [
            v.strip()
            for v in value.split(',')
        ]
        filters = [
            (expression_filter, value)
            for value in values
            if value
        ]
        qs.extend(filters)
        qs.drop(list_filter)
    return qs


def convert_expression_ids_to_expression_filters(qs):
    expression_ids = qs.param_values_to_list(
        params=qs.get_key_filters(
            key='expressionID'
        )
    )
    for expression_id in expression_ids:
        qs.extend(
            EXPRESSION_IDS_MAP.get(
                expression_id,
                {}
            ).get(
                'filters',
                []
            )
        )
    qs.drop('expressionID')
    return qs
