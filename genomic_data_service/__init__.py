from flask import Flask

from genomic_data_service.searches.configs import add_registry
from genomic_data_service.rnaseq.client import add_rna_client
from genomic_data_service.rnaseq.rnaget.api import rnaget_api


def is_web_app():
    return ('FLASK_APP' in environ)

app = Flask(__name__)
app.register_blueprint(rnaget_api)
add_registry(app)
add_rna_client(app)

import genomic_data_service.errors
import genomic_data_service.rnaseq.views
