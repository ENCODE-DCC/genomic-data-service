from flask import current_app
from flask import request

from snosearch.adapters.flask.requests import RequestAdapter
from snosearch.adapters.flask.responses import ResponseAdapter


def make_search_request():
    registry = current_app.registry
    search_request = RequestAdapter(request)
    search_request.registry = registry
    search_request.response = ResponseAdapter()
    return search_request
