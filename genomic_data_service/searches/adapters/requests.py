from flask import Request
from werkzeug.datastructures import ImmutableOrderedMultiDict


class ArgsAdapter:

    def __init__(self, args):
        self.args = args

    def __iter__(self):
        return self.args.__iter__()

    def items(self):
        return self.args.items(multi=True)

    def getall(self, key):
        return self.args.getlist(key)


class RequestAdapter:

    def __init__(self, request):
        self._request = request

    @property
    def params(self):
        return ArgsAdapter(
            self._request.args
        )

    def __setitem__(self, key, value):
        Request.parameter_storage_class = ImmutableOrderedMultiDict
        self._request = Request({key: value})

    def __getitem__(self, key):
        return self._request.environ[key]

    @property
    def environ(self):
        return self

    @property
    def query_string(self):
        return self._request.query_string.decode('utf-8')

    @query_string.setter
    def query_string(self, value):
        self.__setitem__('QUERY_STRING', value)

    def copy(self):
        return RequestAdapter(
            Request(
                self._request.environ
            )
        )
