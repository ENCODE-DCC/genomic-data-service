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
