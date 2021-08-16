from flask import Request


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

    def copy(self):
        return RequestAdapter(
            Request(
                self._request.environ
            )
        )
