from flask import abort

from genomic_data_service.rnaseq.rnaget.constants import BLOCK_IF_NONE_FILTERS
from genomic_data_service.rnaseq.rnaget.constants import DATASET_FROM_TO_FIELD_MAP
from genomic_data_service.rnaseq.rnaget.constants import DEFAULT_EXPRESSION_ID
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


def convert_study_ids_to_expression_filters(qs):
    study_ids = qs.param_values_to_list(
        params=qs.get_key_filters(
            key='studyID'
        )
    )
    for study_id in study_ids:
        qs.append(
            ('dataset.@id', f'/experiments/{study_id}/')
        )
    qs.drop('studyID')
    return qs


def maybe_add_default_expression_id(qs):
    must_have_filters = qs.get_keys_filters(
        keys=ADD_DEFAULT_IF_NONE_FILTERS
    )
    if not must_have_filters:
        qs.append(
            ('expressionID', DEFAULT_EXPRESSION_ID)
        )
    return qs


def maybe_block_request(qs):
    format_ = qs.get_one_value(
        params=qs.get_key_filters(
            key='format'
        )
    )
    must_have_filters = qs.get_keys_filters(
        keys=BLOCK_IF_NONE_FILTERS
    )
    if format_ == 'tsv' and not must_have_filters:
        abort(400, 'Must filter by feature (gene) or sample property')
    return qs
