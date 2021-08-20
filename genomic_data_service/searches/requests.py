from flask import current_app
from flask import request as current_request

from snosearch.adapters.flask.requests import RequestAdapter
from snosearch.adapters.flask.responses import ResponseAdapter


def make_search_request(request=None):
    if request is None:
        request = current_request
    registry = current_app.registry
    if not isinstance(request, RequestAdapter):
        request = RequestAdapter(request)
    search_request = request
    search_request.registry = registry
    search_request.response = ResponseAdapter()
    return search_request
