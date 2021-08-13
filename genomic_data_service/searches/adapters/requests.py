class ArgsAdapter:

    def __init__(self, args):
        self.args = args

    def items(self):
        return self.args.items(multi=True)


class RequestAdapter:

    def __init__(self, request):
        self._request = request
        self._params = ArgsAdapter(request.args)

    @property
    def params(self):
        return self._params
        
