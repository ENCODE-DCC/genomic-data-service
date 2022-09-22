from flask import Flask, jsonify, make_response
from os import environ

from genomic_data_service.searches.configs import add_registry
from genomic_data_service.rnaseq.client import add_rna_client
from genomic_data_service.rnaseq.rnaget.api import rnaget_api
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3


def is_web_app():
    return 'FLASK_APP' in environ


app = Flask(__name__)
app.register_blueprint(rnaget_api)


if 'GENOMIC_DATA_SERVICE_SETTINGS' in environ:
    app.config.from_envvar('GENOMIC_DATA_SERVICE_SETTINGS')
else:
    logging.info('[CONFIG] Defaulting to development config')
    app.config.from_pyfile('../config/development.cfg')

add_registry(app)
add_rna_client(app)


if is_web_app():
    opensearch_env = environ['OPENSEARCH']
    if opensearch_env == 'local':
        auth = ('admin', 'admin')
    else:
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, 'us-west-2')
    port = app.config['REGULOME_ES_PORT']
    hosts = app.config['REGULOME_ES_HOSTS']
    regulome_es = OpenSearch(
        hosts=[{'host': hosts[0], 'port': port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        # client_cert = client_cert_path,
        # client_key = client_key_path,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        #ca_certs = ca_certs_path
        connection_class=RequestsHttpConnection,
    )
    port = app.config['REGION_SEARCH_ES_PORT']
    hosts = app.config['REGION_SEARCH_ES_HOSTS']
    region_search_es = OpenSearch(
        hosts=[{'host': hosts[0], 'port': port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        # client_cert = client_cert_path,
        # client_key = client_key_path,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        #ca_certs = ca_certs_path
        connection_class=RequestsHttpConnection,
    )

    app.url_map.strict_slashes = False

    # Enabled endpoints:
    import genomic_data_service.search
    import genomic_data_service.summary
    import genomic_data_service.rnaseq.views
    import genomic_data_service.errors

    @app.route('/healthcheck/', methods=['GET'])
    def healthcheck():
        status = {}
        try:
            status['regulome_es'] = regulome_es.cluster.health()
            status['region_search_es'] = region_search_es.cluster.health()
        except Exception as e:
            status['exception'] = str(e)

        response_out = make_response(
            jsonify(status),
            200,
        )
        response_out.headers = {'Content-Type': 'application/json'}
        return response_out
