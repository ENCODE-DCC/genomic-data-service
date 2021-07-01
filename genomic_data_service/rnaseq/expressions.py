

class Expressions:

    def __init__(self, portal, repository):
        self.portal = portal
        self.repository = repository

    def index(self):
        files = self.portal.get_rna_seq_files()
        self.repository.bulk_load_from_files(
            files
        )
