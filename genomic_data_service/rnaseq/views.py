from genomic_data_service import app

from genomic_data_service.rnaseq.searches import rnaget_report
from genomic_data_service.rnaseq.searches import rnaget_search
from genomic_data_service.rnaseq.searches import rnaget_search_quick
from genomic_data_service.rnaseq.searches import rnaget_expression_matrix


from genomic_data_service.searches.requests import make_search_request


@app.route('/rnaget-search-quick/', methods=['GET'])
def rnaget_search_quick_view():
    search_request = make_search_request()
    return rnaget_search_quick(search_request)


@app.route('/rnaget-search/', methods=['GET'])
def rnaget_search_view():
    search_request = make_search_request()
    return rnaget_search(search_request)


@app.route('/rnaget-report/', methods=['GET'])
def rnaget_report_view():
    search_request = make_search_request()
    return rnaget_report(search_request)


@app.route('/rnaget-expression-matrix/', methods=['GET'])
def rnaget_expression_matrix_view():
    search_request = make_search_request()
    return rnaget_expression_matrix(search_request)
