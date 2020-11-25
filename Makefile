export APP_NAME := genomic_data_service

build:
	python3 -m venv venv
	source venv/bin/activate
	pip3 install -r requirements.txt
	pip3 install -e .
	deactivate & source venv/bin/activate
	python3 ./utils/download_ml_models.py

run:
	FLASK_APP=$(APP_NAME) FLASK_ENV=development flask run -p 5000

clean:
	rm -rf genomic_data_service.egg-info/

test:
	FLASK_APP=$(APP_NAME) FLASK_ENV=test GENOMIC_DATA_SERVICE_SETTINGS=../config/test.cfg pytest

prod:
	FLASK_APP=$(APP_NAME) GENOMIC_DATA_SERVICE_SETTINGS=../config/production.cfg gunicorn -w 4 -b 127.0.0.1:4000 wsgi:app

worker:
	celery -A genomic_data_service.region_indexer_task worker --loglevel=INFO

flower:
	flower -A genomic_data_service.region_indexer_task --address=127.0.0.1 --port=5555 --persistent=True --db=indexer_logs --max_tasks=1000000

index:
	python3 genomic_data_service/region_indexer.py
