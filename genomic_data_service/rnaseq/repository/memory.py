class Memory:
    def __init__(self):
        self.data = []

    def load(self, item):
        self.data.append(item)

    def bulk_load(self, items):
        self.data.extend(items)

    def bulk_load_from_files(self, files):
        for file_ in files:
            self.data.extend(file_.as_documents())

    def clear(self):
        self.data = []
