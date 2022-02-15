from genomic_data_service.rnaseq.tests.elasticsearch.fixtures import start_elasticsearch


def run_elasticsearch():
    with start_elasticsearch() as es:
        while True:
            pass


if __name__ == '__main__':
    run_elasticsearch()
