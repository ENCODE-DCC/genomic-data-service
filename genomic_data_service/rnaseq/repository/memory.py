

class Memory:
 
    def __init__(self):
        self._data = []

    def add(self, item):
        self._data.append(item)

    def bulk_add(self, items):
        self._data.extend(items)
