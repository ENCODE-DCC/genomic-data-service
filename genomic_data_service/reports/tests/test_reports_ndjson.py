import pytest


def test_reports_ndjson_ndjson_generator():
    from genomic_data_service.reports.ndjson import NDJSONGenerator
    from flask import Response

    ndjg = NDJSONGenerator([])
    assert isinstance(ndjg, NDJSONGenerator)
    values = [
        {"a": "b"},
        {"x": {"y": "z\nttt"}},
        {"and": ["another", {"thing": "nested"}]},
    ]
    ndjg = NDJSONGenerator((v for v in values))
    actual = list(ndjg.stream())
    expected = [
        '{"a": "b"}\n',
        '{"x": {"y": "z\\nttt"}}\n',
        '{"and": ["another", {"thing": "nested"}]}\n',
    ]
    assert actual == expected
    ndjg = NDJSONGenerator((v for v in values))
    r = ndjg.as_response()
    assert isinstance(r, Response)
    assert r.mimetype == "application/x-ndjson"
    assert r.get_data() == (
        b'{"a": "b"}\n{"x": {"y": "z\\nttt"}}\n'
        b'{"and": ["another", {"thing": "nested"}]}\n'
    )
