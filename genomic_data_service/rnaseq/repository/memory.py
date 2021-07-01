

class Memory:
 
    def __init__(self):
        self._data = []

    def load(self, item):
        self._data.append(item)

    def bulk_load(self, items):
        self._data.extend(items)

    def bulk_load_from_files(self, files):
        for file_ in files:
            self._data.extend(
                file_.as_documents()
            )

    def clear(self):
        self._data = []
