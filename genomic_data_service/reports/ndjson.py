import json

from flask import Response


class NDJSONGenerator:
    """
    Streams list[dict] as newline-delimited JSON.
    """

    NEWLINE = "\n"
    MIMETYPE = "application/x-ndjson"

    def __init__(self, values):
        self.values = values

    def stream(self):
        for value in self.values:
            yield json.dumps(value) + "\n"

    def as_response(self):
        return Response(
            self.stream(),
            mimetype=self.MIMETYPE,
        )
